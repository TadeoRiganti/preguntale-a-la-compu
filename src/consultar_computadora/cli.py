import time
import argparse
import warnings
from collections import deque
import numpy as np
import sounddevice as sd

warnings.filterwarnings("ignore")

from faster_whisper import WhisperModel
from kokoro import KPipeline

from .llm import OLLAMA_URL, generar_respuesta, ollama_disponible, precargar_ollama
from .tts import agrupar_oraciones, hablar_respuesta

WAKE_WORDS = ["computadora", "computador", "compu"]
SAMPLE_RATE = 16000
UMBRAL_SILENCIO = 0.022
SEGUNDOS_SILENCIO = 1.6


def emitir_tono(frecuencia=880, duracion=0.12):
    """Genera un breve sonido de confirmación al detectar 'Computadora'."""
    t = np.linspace(0, duracion, int(24000 * duracion), False)
    tono = 0.2 * np.sin(2 * np.pi * frecuencia * t) * np.hanning(len(t))
    sd.play(tono.astype(np.float32), 24000)
    sd.wait()


def grabar_frase(max_segundos=None, segundos_corte=SEGUNDOS_SILENCIO):
    bloque_duracion = 0.1
    muestras_bloque = int(SAMPLE_RATE * bloque_duracion)
    pre_buffer = deque(maxlen=8)
    bloques = []
    bloques_silencio = 0
    max_bloques_silencio = int(segundos_corte / bloque_duracion)
    max_bloques_totales = int(max_segundos / bloque_duracion) if max_segundos else None
    empezo_a_hablar = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        while True:
            audio_chunk, _ = stream.read(muestras_bloque)
            volumen = np.linalg.norm(audio_chunk) / np.sqrt(len(audio_chunk))

            if not empezo_a_hablar:
                pre_buffer.append(audio_chunk)
                if volumen > UMBRAL_SILENCIO:
                    empezo_a_hablar = True
                    bloques.extend(pre_buffer)
                    bloques_silencio = 0
            else:
                bloques.append(audio_chunk)
                if max_bloques_totales and len(bloques) >= max_bloques_totales:
                    break
                if volumen > UMBRAL_SILENCIO:
                    bloques_silencio = 0
                else:
                    bloques_silencio += 1
                    if bloques_silencio >= max_bloques_silencio:
                        break

    audio = np.concatenate(bloques).flatten()
    pico = np.max(np.abs(audio))
    if pico > 0:
        audio = audio / pico * 0.9
    return audio


def cargar_whisper(nombre_modelo):
    """Intenta cargar desde caché local; si no existe, lo descarga."""
    try:
        return WhisperModel(nombre_modelo, device="cpu", compute_type="int8", local_files_only=True)
    except Exception:
        print(f"📥 Descargando modelo Whisper '{nombre_modelo}' por única vez...")
        return WhisperModel(nombre_modelo, device="cpu", compute_type="int8")


def main():
    parser = argparse.ArgumentParser(description="Asistente continuo activado por voz ('Computadora')")
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
    args = parser.parse_args()

    if not ollama_disponible():
        print(f"❌ Error: no se pudo conectar con Ollama en {OLLAMA_URL}. "
              "¿Está instalado y el servicio corriendo?")
        return

    print("Cargando modelos en memoria...")
    whisper_wake = cargar_whisper("tiny")
    whisper_main = whisper_wake if args.modelo == "tiny" else cargar_whisper(args.modelo)
    kokoro_pipeline = KPipeline(lang_code='e', repo_id='hexgrad/Kokoro-82M')

    try:
        precargar_ollama(args.ollama)
    except Exception as e:
        print(f"❌ Error: Ollama no pudo cargar el modelo '{args.ollama}' ({e}). "
              f"¿Hiciste 'ollama pull {args.ollama}'?")
        return

    print(f"\n🟢 La computadora está activa (Whisper: {args.modelo} | Ollama: {args.ollama}).")
    print("   Di 'Computadora' para preguntar (Ctrl+C para salir).\n")

    try:
        while True:
            audio_wake = grabar_frase(max_segundos=2.2, segundos_corte=0.7)
            segs, _ = whisper_wake.transcribe(audio_wake, language="es", beam_size=1, vad_filter=True)
            texto_detectado = " ".join([s.text for s in segs]).lower().strip()

            if any(w in texto_detectado for w in WAKE_WORDS):
                emitir_tono(880, 0.12)
                print("🎤 Ahora te estoy escuchando... ¿Qué querías saber?")

                audio_pregunta = grabar_frase(segundos_corte=SEGUNDOS_SILENCIO)
                segs_q, _ = whisper_main.transcribe(
                    audio_pregunta,
                    language="es",
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(threshold=0.35, min_silence_duration_ms=250, speech_pad_ms=400),
                    initial_prompt="Computadora, esta es una consulta en español."
                )
                pregunta = " ".join([s.text for s in segs_q]).strip()

                if not pregunta:
                    emitir_tono(440, 0.15)
                    print("⏳ No escuché la pregunta. Volviendo a espera...\n")
                    continue

                print(f"🗣️  Tú: {pregunta}")
                print("🤖 Computadora: ", end="", flush=True)

                try:
                    oraciones = agrupar_oraciones(generar_respuesta(args.ollama, pregunta))
                    hablo = hablar_respuesta(oraciones, kokoro_pipeline, args.voz)
                    print("\n" if hablo else "(respuesta vacía)\n")
                except Exception as e:
                    print(f"\n❌ Error al generar la respuesta: {e}\n")

                time.sleep(0.4)
                print("🟢 Esperando 'Computadora'...")

    except KeyboardInterrupt:
        print("\n👋 Ya apagué mis oídos!")


if __name__ == "__main__":
    main()
