"""Reconocimiento de voz con faster-whisper."""
import re
import unicodedata

from faster_whisper import WhisperModel

WAKE_WORDS = ["computadora", "computador", "compu"]


def cargar_whisper(nombre_modelo):
    """Intenta cargar desde caché local; si no existe, lo descarga."""
    try:
        return WhisperModel(nombre_modelo, device="cpu", compute_type="int8", local_files_only=True)
    except Exception:
        print(f"📥 Descargando modelo Whisper '{nombre_modelo}' por única vez...")
        return WhisperModel(nombre_modelo, device="cpu", compute_type="int8")


def normalizar(texto):
    """Minúsculas, sin tildes ni puntuación y con los espacios colapsados (para comparar textos)."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^\w\s]|_", " ", sin_tildes.lower()).split())


def palabras_detectadas(texto, palabras=None):
    """Devuelve las palabras o frases de activación que aparecen en el texto.

    Compara sin distinguir mayúsculas, tildes ni puntuación: "Oye, computadora." coincide con "oye computadora".
    """
    texto = normalizar(texto)
    candidatas = WAKE_WORDS if palabras is None else palabras
    return [w for w in candidatas if (n := normalizar(w)) and n in texto]


def resolver_palabras(candidatas):
    """Palabras de activación a usar: las que pidió el usuario (sin vacías) o las predeterminadas."""
    if not candidatas:
        return list(WAKE_WORDS)
    palabras = [p.strip() for p in candidatas if normalizar(p)]
    if not palabras:
        raise ValueError("la palabra de activación no puede estar vacía")
    return palabras


def transcribir_activacion(modelo, audio):
    """Transcribe un fragmento corto para buscar la palabra de activación (rápido, beam_size=1)."""
    segs, _ = modelo.transcribe(audio, language="es", beam_size=1, vad_filter=True)
    return " ".join([s.text for s in segs]).lower().strip()


def transcribir_pregunta(modelo, audio, palabra="Computadora"):
    """Transcribe la pregunta del usuario (más preciso, beam_size=5).

    `palabra` se usa en el texto de contexto que se le da a Whisper (initial_prompt).
    """
    segs, _ = modelo.transcribe(
        audio,
        language="es",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(threshold=0.35, min_silence_duration_ms=250, speech_pad_ms=400),
        initial_prompt=f"{palabra.capitalize()}, esta es una consulta en español."
    )
    return " ".join([s.text for s in segs]).strip()
