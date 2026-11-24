"""Cronómetro opcional para medir cuánto tarda cada etapa (bandera --metricas)."""
import time


def _fmt(segundos):
    return "n/d" if segundos is None else f"{segundos:.2f}s"


class Metricas:
    """Registra marcas de tiempo y arma un resumen.

    El reloj arranca al crearla, justo cuando termina de grabarse la pregunta.
    """

    def __init__(self):
        self.t0 = time.perf_counter()
        self.marcas = {}
        self.ollama = {}  # estadísticas del último mensaje del streaming de Ollama

    def marcar(self, nombre):
        """Guarda el instante de un hito (solo la primera vez que se marca)."""
        self.marcas.setdefault(nombre, time.perf_counter())

    def registrar_ollama(self, dato):
        """Guarda las estadísticas que Ollama manda en el último mensaje del streaming."""
        self.ollama = {k: dato.get(k) for k in ("eval_count", "eval_duration", "load_duration")}

    def _partes_ollama(self):
        partes = []
        tokens, duracion = self.ollama.get("eval_count"), self.ollama.get("eval_duration")
        if tokens and duracion:
            partes.append(f"{tokens / (duracion / 1e9):.1f} tok/s ({tokens} tokens)")
        carga = (self.ollama.get("load_duration") or 0) / 1e9
        if carga > 0.1:
            partes.append(f"carga del modelo {carga:.2f}s")
        return partes

    def desde(self, hito, origen=None):
        """Segundos entre dos hitos (por defecto, desde el inicio); None si falta alguno."""
        fin = self.marcas.get(hito)
        inicio = self.t0 if origen is None else self.marcas.get(origen)
        if fin is None or inicio is None:
            return None
        return fin - inicio

    def resumen(self, silencio):
        """`silencio` es la espera configurada para dar por terminada la pregunta (SEGUNDOS_SILENCIO)."""
        audio = self.desde("primer_audio")
        espera = None if audio is None else silencio + audio
        linea = (f"⏱️  Espera {_fmt(espera)} (silencio {silencio:.2f}s + 1er audio {_fmt(audio)}) "
                 f"| total {_fmt(self.desde('fin'))}")
        partes = [
            f"STT {_fmt(self.desde('stt_fin'))}",
            f"1er token {_fmt(self.desde('primer_token', 'llm_inicio'))}",
            f"1ª oración {_fmt(self.desde('primera_oracion', 'llm_inicio'))}",
            f"síntesis 1ª oración {_fmt(self.desde('primera_sintesis', 'primera_oracion'))}",
        ]
        partes += self._partes_ollama()
        return linea + "\n    " + " | ".join(partes)
