"""Subcomando 'transcribir': transcribe en vivo lo que capta el micrófono (depuración).

Usa el mismo audio, modelo y lógica de detección que el asistente, para ver qué entiende
Whisper y si el texto activaría el asistente.
"""
import re
import time

from .audio import (ACTIVACION_MAX_SEGUNDOS, ACTIVACION_SEGUNDOS_SILENCIO, SAMPLE_RATE,
                    SEGUNDOS_SILENCIO, grabar_frase)
from .stt import (cargar_whisper, normalizar, palabras_detectadas, transcribir_activacion,
                  transcribir_pregunta)


def agregar_argumentos(parser):
    """Define las banderas del subcomando (los nombres internos no chocan con los del asistente)."""
    parser.add_argument(
        "--modo",
        choices=["activacion", "pregunta"],
        default="activacion",
        help="activacion: audio corto y modelo liviano, como al esperar la palabra de activación; "
             "pregunta: como al grabar la pregunta (default: activacion)"
    )
    parser.add_argument(
        "-m", "--modelo",
        dest="modelo_stt",
        choices=["tiny", "base", "small", "turbo"],
        help="Modelo Whisper (default: tiny en modo activacion, base en modo pregunta)"
    )
    parser.add_argument(
        "-p", "--palabra",
        dest="palabras_prueba",
        action="append",
        help="Palabra o frase de activación a probar (reemplaza a las predeterminadas; se puede repetir; "
             "las frases van entre comillas)"
    )


def describir_coincidencias(texto, coincidencias):
    """Indica qué palabras del texto coincidieron con las palabras de activación (útil para falsos positivos)."""
    tokens = list(dict.fromkeys(t.lower() for t in re.findall(r"\w+", texto)))
    partes = []
    for token in tokens:
        normal = normalizar(token)
        halladas = [w for w in coincidencias if " " not in normalizar(w) and normalizar(w) in normal]
        if halladas:
            partes.append(f'"{token}" ← {", ".join(halladas)}')
    partes += [f'frase "{w}"' for w in coincidencias if " " in normalizar(w)]
    return "; ".join(partes)

def ejecutar(args, palabras):
    nombre_modelo = args.modelo_stt or ("tiny" if args.modo == "activacion" else "base")

    print(f"Cargando Whisper '{nombre_modelo}'...")
    modelo = cargar_whisper(nombre_modelo)
    print(f"\n🎙️  Modo {args.modo} · Whisper '{nombre_modelo}'. Hablá y mirá qué entiende (Ctrl+C para salir).")
    if args.modo == "activacion":
        lista = ", ".join(f'"{p}"' for p in palabras)
        print(f"   Palabras de activación: {lista}")
    print()

    n = 0
    try:
        while True:
            if args.modo == "activacion":
                audio = grabar_frase(max_segundos=ACTIVACION_MAX_SEGUNDOS,
                                     segundos_corte=ACTIVACION_SEGUNDOS_SILENCIO)
            else:
                audio = grabar_frase(segundos_corte=SEGUNDOS_SILENCIO)

            inicio = time.perf_counter()
            if args.modo == "activacion":
                texto = transcribir_activacion(modelo, audio)
            else:
                texto = transcribir_pregunta(modelo, audio, palabras[0])
            tardo = time.perf_counter() - inicio

            n += 1
            print(f"[{n}] {len(audio) / SAMPLE_RATE:.1f} s de audio · transcripción {tardo:.2f}s")
            if texto:
                print(f'    Texto: "{texto}"')
            else:
                print("    (Whisper no devolvió texto: no detectó voz en el audio)")

            if args.modo == "activacion":
                coincidencias = palabras_detectadas(texto, palabras)
                if coincidencias:
                    print(f"    ✅ Activaría el asistente: {describir_coincidencias(texto, coincidencias)}")
                else:
                    print("    ❌ No activaría el asistente")
            print()

    except KeyboardInterrupt:
        print("\n👋 Listo.")
