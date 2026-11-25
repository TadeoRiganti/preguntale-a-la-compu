"""Captura de micrófono con detección de silencio y tono de confirmación."""
from collections import deque
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
UMBRAL_SILENCIO = 0.022
SEGUNDOS_SILENCIO = 1.6
ACTIVACION_MAX_SEGUNDOS = 2.2       # audio máximo con el que se busca la palabra de activación
ACTIVACION_SEGUNDOS_SILENCIO = 0.7  # silencio que cierra esa grabación


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
