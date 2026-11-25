"""Reconocimiento de voz con faster-whisper."""
from faster_whisper import WhisperModel

WAKE_WORDS = ["computadora", "computador", "compu"]


def cargar_whisper(nombre_modelo):
    """Intenta cargar desde caché local; si no existe, lo descarga."""
    try:
        return WhisperModel(nombre_modelo, device="cpu", compute_type="int8", local_files_only=True)
    except Exception:
        print(f"📥 Descargando modelo Whisper '{nombre_modelo}' por única vez...")
        return WhisperModel(nombre_modelo, device="cpu", compute_type="int8")


def palabras_detectadas(texto, palabras=None):
    """Devuelve las palabras de activación que aparecen en el texto (ya en minúsculas)."""
    return [w for w in (WAKE_WORDS if palabras is None else palabras) if w in texto]


def transcribir_activacion(modelo, audio):
    """Transcribe un fragmento corto para buscar la palabra de activación (rápido, beam_size=1)."""
    segs, _ = modelo.transcribe(audio, language="es", beam_size=1, vad_filter=True)
    return " ".join([s.text for s in segs]).lower().strip()


def transcribir_pregunta(modelo, audio):
    """Transcribe la pregunta del usuario (más preciso, beam_size=5)."""
    segs, _ = modelo.transcribe(
        audio,
        language="es",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(threshold=0.35, min_silence_duration_ms=250, speech_pad_ms=400),
        initial_prompt="Computadora, esta es una consulta en español."
    )
    return " ".join([s.text for s in segs]).strip()
