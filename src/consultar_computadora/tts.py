"""Corte de la respuesta en oraciones y reproducción por voz (Kokoro)."""
import re
import queue
from contextlib import closing
import threading
import sounddevice as sd

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


def hablar_respuesta(oraciones, kokoro_pipeline, voz, metricas=None):
    """Sintetiza y reproduce las oraciones en paralelo, a medida que van llegando.

    Un hilo consume las oraciones (por ejemplo, las del streaming de Ollama) y las sintetiza
    con Kokoro mientras el hilo principal reproduce el audio ya listo.
    Devuelve True si se dijo algo. Si se pasa `metricas`, registra cuándo está lista
    la primera oración, cuándo Kokoro entrega su primer audio y cuándo empieza a sonar.

    Si se interrumpe (por ejemplo con Ctrl+C), frena el audio, le avisa al hilo de síntesis para que
    se detenga y vuelve a lanzar la interrupción sin esperar a ese hilo. Kokoro no se puede cortar
    a mitad de una oración: la que estaba sintetizando termina en segundo plano y se descarta.
    """
    cola = queue.Queue(maxsize=2)
    errores = []
    cancelado = threading.Event()

    def encolar(audio):
        """Pone el audio en la cola. Devuelve False si se canceló mientras esperaba lugar."""
        while not cancelado.is_set():
            try:
                cola.put(audio, timeout=0.1)
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
                for _, _, audio in kokoro_pipeline(oracion, voice=voz, speed=1.0):
                    if metricas:
                        metricas.marcar("primera_sintesis")
                    if not encolar(audio):
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
        while (audio := cola.get()) is not None:
            hablo = True
            if metricas:
                metricas.marcar("primer_audio")
            sd.play(audio, 24000)
            sd.wait()
    except BaseException:  # Ctrl+C u otro error mientras se esperaba o reproducía
        cancelado.set()
        sd.stop()
        raise
    hilo.join()

    if errores:
        raise errores[0]
    return hablo
