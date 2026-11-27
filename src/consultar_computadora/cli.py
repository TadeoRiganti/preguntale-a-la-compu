import time
import argparse
import warnings

warnings.filterwarnings("ignore")

from . import transcribir
from .audio import (ACTIVACION_MAX_SEGUNDOS, ACTIVACION_SEGUNDOS_SILENCIO, SEGUNDOS_SILENCIO,
                    emitir_tono, grabar_frase)
from .llm import OLLAMA_URL, generar_respuesta, ollama_disponible, precargar_ollama
from .metricas import Metricas
from .stt import (cargar_whisper, palabras_detectadas, resolver_palabras, transcribir_activacion,
                  transcribir_pregunta)
from .tts import agrupar_oraciones, hablar_respuesta


def main():
    parser = argparse.ArgumentParser(
        description="Asistente continuo activado por voz ('Computadora')",
        usage="%(prog)s [opciones]\n       %(prog)s transcribir [opciones]",
    )
    parser.add_argument(
        "-m", "--modelo",
        choices=["base", "small", "turbo"],
        default="base",
        help="Modelo Whisper para transcribir la pregunta (default: base)"
    )
    parser.add_argument(
        "--ollama",
        default="gemma4:e4b",
        help="Modelo de Ollama a utilizar (default: gemma4:e4b)"
    )
    parser.add_argument(
        "-v", "--voz",
        default="ef_dora",
        help="Voz en español de Kokoro: ef_dora, em_alex, em_santa (default: ef_dora)"
    )
    parser.add_argument(
        "--metricas",
        action="store_true",
        help="Muestra los tiempos de cada etapa después de cada respuesta"
    )
    parser.add_argument(
        "-p", "--palabra",
        action="append",
        help="Palabra o frase de activación (reemplaza a las predeterminadas; se puede repetir; "
             "las frases van entre comillas)"
    )
    transcribir.agregar_argumentos(
        parser.add_subparsers(dest="comando", metavar="comando").add_parser(
            "transcribir",
            help="Transcribe en vivo lo que capta el micrófono (para probar palabras de activación)",
        )
    )
    args = parser.parse_args()
    candidatas = args.palabra
    if args.comando == "transcribir":
        candidatas = args.palabras_prueba or args.palabra  # --palabra vale antes o después del subcomando
    try:
        palabras = resolver_palabras(candidatas)
    except ValueError as e:
        parser.error(str(e))

    if args.comando == "transcribir":
        transcribir.ejecutar(args, palabras)
        return

    decir = " o ".join(f"'{p}'" for p in palabras)

    if not ollama_disponible():
        print(f"❌ Error: no se pudo conectar con Ollama en {OLLAMA_URL}. "
              "¿Está instalado y el servicio corriendo?")
        return

    print("Cargando modelos en memoria...")
    whisper_wake = cargar_whisper("tiny")
    whisper_main = whisper_wake if args.modelo == "tiny" else cargar_whisper(args.modelo)
    from kokoro import KPipeline  # acá y no arriba: 'transcribir' no necesita cargar torch
    kokoro_pipeline = KPipeline(lang_code='e', repo_id='hexgrad/Kokoro-82M')

    try:
        precargar_ollama(args.ollama)
    except Exception as e:
        print(f"❌ Error: Ollama no pudo cargar el modelo '{args.ollama}' ({e}). "
              f"¿Hiciste 'ollama pull {args.ollama}'?")
        return

    print(f"\n🟢 La computadora está activa (Whisper: {args.modelo} | Ollama: {args.ollama}).")
    print(f"   Di {decir} para preguntar.")
    print("   Ctrl+C: cancela la respuesta en curso; en espera, cierra el programa.\n")

    escuchar_directo = False  # tras cancelar una respuesta se escucha otra pregunta sin pedir la palabra
    try:
        while True:
            if not escuchar_directo:
                audio_wake = grabar_frase(max_segundos=ACTIVACION_MAX_SEGUNDOS,
                                          segundos_corte=ACTIVACION_SEGUNDOS_SILENCIO)
                texto_detectado = transcribir_activacion(whisper_wake, audio_wake)

            if escuchar_directo or palabras_detectadas(texto_detectado, palabras):
                escuchar_directo = False
                emitir_tono(880, 0.12)
                print("🎤 Ahora te estoy escuchando... ¿Qué querías saber?")

                audio_pregunta = grabar_frase(segundos_corte=SEGUNDOS_SILENCIO)
                metricas = Metricas() if args.metricas else None
                pregunta = transcribir_pregunta(whisper_main, audio_pregunta, palabras[0])
                if metricas:
                    metricas.marcar("stt_fin")

                if not pregunta:
                    emitir_tono(440, 0.15)
                    print("⏳ No escuché la pregunta. Volviendo a espera...\n")
                    continue

                print(f"🗣️  Tú: {pregunta}")
                print("🤖 Computadora: ", end="", flush=True)

                try:
                    oraciones = agrupar_oraciones(generar_respuesta(args.ollama, pregunta, metricas))
                    hablo = hablar_respuesta(oraciones, kokoro_pipeline, args.voz, metricas)
                    if metricas:
                        metricas.marcar("fin")
                    print("\n" if hablo else "(respuesta vacía)\n")
                    if metricas and hablo:
                        print(metricas.resumen(SEGUNDOS_SILENCIO) + "\n")
                except KeyboardInterrupt:
                    print("\n✋ Respuesta cancelada.\n")
                    escuchar_directo = True
                    continue
                except Exception as e:
                    print(f"\n❌ Error al generar la respuesta: {e}\n")

                time.sleep(0.4)
                print(f"🟢 Esperando {decir}...")

    except KeyboardInterrupt:
        print("\n👋 Ya apagué mis oídos!")


if __name__ == "__main__":
    main()
