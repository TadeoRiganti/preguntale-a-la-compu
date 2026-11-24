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

    def marcar(self, nombre):
        """Guarda el instante de un hito (solo la primera vez que se marca)."""
        self.marcas.setdefault(nombre, time.perf_counter())

    def desde(self, hito, origen=None):
        """Segundos entre dos hitos (por defecto, desde el inicio); None si falta alguno."""
        fin = self.marcas.get(hito)
        inicio = self.t0 if origen is None else self.marcas.get(origen)
        if fin is None or inicio is None:
            return None
        return fin - inicio

    def resumen(self, silencio):
        """`silencio` es la espera configurada para dar por terminada la pregunta (SEGUNDOS_SILENCIO)."""
        return (f"⏱️  silencio {silencio:.2f}s | STT {_fmt(self.desde('stt_fin'))} "
                f"| total {_fmt(self.desde('fin'))}")
