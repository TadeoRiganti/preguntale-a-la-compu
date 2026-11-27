"""Corte de la respuesta en oraciones y reproducción por voz (Piper)."""
import os
import re
import queue
from contextlib import closing
import threading
from pathlib import Path
import sounddevice as sd

VOZ_PREDETERMINADA = "es_ES-davefx-medium"
DIRECTORIO_VOCES = (Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
                    / "consultar-computadora" / "voces")
MIN_CARACTERES_ORACION = 25    # evita mandar al TTS fragmentos demasiado cortos
FIN_ORACION = re.compile(r"(?<=[.!?…])\s+|\n+")


def agrupar_oraciones(trozos):
    """Agrupa el texto en streaming en oraciones completas (y sin símbolos de markdown).

    Si quien consume deja de pedir oraciones y cierra este generador, cierra también el de origen
    (así se corta la conexión con Ollama y deja de generar).
    """
    with closing(trozos):
        pendiente = ""
        buffer = ""
        for trozo in trozos:
            buffer += re.sub(r"[*#_`]", "", trozo)
            partes = FIN_ORACION.split(buffer)
            buffer = partes.pop()  # último fragmento: puede estar incompleto
            for parte in partes:
                pendiente = f"{pendiente} {parte}".strip()
                if len(pendiente) >= MIN_CARACTERES_ORACION:
                    yield pendiente
                    pendiente = ""
        resto = f"{pendiente} {buffer}".strip()
        if resto:
            yield resto


def cargar_voz(nombre):
    """Carga una voz de Piper; si no está en DIRECTORIO_VOCES, la descarga.

    Antes de devolverla sintetiza un texto que no se reproduce, para que la primera
    respuesta no pague la inicialización.
    """
    # Se importa acá y no arriba: 'transcribir' no necesita cargar Piper
    from piper import PiperVoice
    from piper.download_voices import download_voice

    DIRECTORIO_VOCES.mkdir(parents=True, exist_ok=True)
    if not all((DIRECTORIO_VOCES / f"{nombre}{ext}").exists() for ext in (".onnx", ".onnx.json")):
        print(f"📥 Descargando la voz de Piper '{nombre}' por única vez...")
    # Si los archivos ya están no usa la red. Devuelve el nombre actual (algunas voces se renombraron)
    nombre = download_voice(nombre, DIRECTORIO_VOCES)
    voz = PiperVoice.load(DIRECTORIO_VOCES / f"{nombre}.onnx")
    for _ in voz.synthesize("Hola."):
        pass
    return voz


def crear_sintetizador(voz):
    """Devuelve una función que convierte una oración en fragmentos (audio, frecuencia de muestreo)."""
    def sintetizar(oracion):
        for fragmento in voz.synthesize(oracion):
            yield fragmento.audio_float_array, fragmento.sample_rate
    return sintetizar


def hablar_respuesta(oraciones, sintetizar, metricas=None):
    """Sintetiza y reproduce las oraciones en paralelo, a medida que van llegando.

    Un hilo consume las oraciones (por ejemplo, las del streaming de Ollama) y las sintetiza
    con `sintetizar` mientras el hilo principal reproduce el audio ya listo.
    Devuelve True si se dijo algo. Si se pasa `metricas`, registra cuándo está lista
    la primera oración, cuándo se obtiene su primer audio y cuándo empieza a sonar.

    Si se interrumpe (por ejemplo con Ctrl+C), frena el audio, le avisa al hilo de síntesis para que
    se detenga y vuelve a lanzar la interrupción sin esperar a ese hilo. Piper no se puede cortar
    a mitad de una oración: la que estaba sintetizando termina en segundo plano y se descarta.
    """
    cola = queue.Queue(maxsize=2)
    errores = []
    cancelado = threading.Event()

    def encolar(fragmento):
        """Pone el fragmento en la cola. Devuelve False si se canceló mientras esperaba lugar."""
        while not cancelado.is_set():
            try:
                cola.put(fragmento, timeout=0.1)
                return True
            except queue.Full:
                pass
        return False

    def productor():
        try:
            for oracion in oraciones:
                if cancelado.is_set():
                    return
                if metricas:
                    metricas.marcar("primera_oracion")
                print(oracion, end=" ", flush=True)
                for fragmento in sintetizar(oracion):
                    if metricas:
                        metricas.marcar("primera_sintesis")
                    if not encolar(fragmento):
                        return
        except Exception as e:
            errores.append(e)
        finally:
            cerrar = getattr(oraciones, "close", None)
            if cerrar:
                cerrar()  # corta la conexión con Ollama si todavía estaba generando
            encolar(None)

    hilo = threading.Thread(target=productor, daemon=True)
    hilo.start()

    hablo = False
    try:
        while (fragmento := cola.get()) is not None:
            audio, frecuencia = fragmento
            hablo = True
            if metricas:
                metricas.marcar("primer_audio")
            sd.play(audio, frecuencia)
            sd.wait()
    except BaseException:  # Ctrl+C u otro error mientras se esperaba o reproducía
        cancelado.set()
        sd.stop()
        raise
    hilo.join()

    if errores:
        raise errores[0]
    return hablo
