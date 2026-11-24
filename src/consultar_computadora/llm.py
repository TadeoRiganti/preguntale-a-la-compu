"""Cliente de la API local de Ollama (solo con la biblioteca estándar)."""
import os
import json
import urllib.request

OLLAMA_KEEP_ALIVE = "30m"      # cuánto queda el modelo en memoria tras la última consulta
MAX_TOKENS_RESPUESTA = 300     # tope de tokens por respuesta (respuestas habladas cortas)
PROMPT_SISTEMA = (
    "Responde en español de forma clara y concisa, en texto plano, "
    "sin usar listas, asteriscos ni símbolos de markdown."
)


def obtener_url_ollama():
    """Respeta OLLAMA_HOST si está definida; si no, usa el puerto por defecto."""
    host = os.environ.get("OLLAMA_HOST", "").strip() or "127.0.0.1:11434"
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host.replace("0.0.0.0", "127.0.0.1").rstrip("/")


OLLAMA_URL = obtener_url_ollama()


def ollama_post(ruta, cuerpo, timeout=120):
    solicitud = urllib.request.Request(
        OLLAMA_URL + ruta,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(solicitud, timeout=timeout)


def ollama_disponible():
    try:
        urllib.request.urlopen(OLLAMA_URL + "/api/version", timeout=3).close()
        return True
    except Exception:
        return False


def precargar_ollama(modelo):
    """Carga el modelo en memoria sin generar texto, para que la primera pregunta no pague la carga."""
    cuerpo = {"model": modelo, "keep_alive": OLLAMA_KEEP_ALIVE, "stream": False}
    with ollama_post("/api/generate", cuerpo, timeout=300):
        pass


def generar_respuesta(modelo, pregunta, metricas=None):
    """Pide la respuesta en streaming y va entregando trozos de texto a medida que llegan.

    Si se pasa `metricas`, registra cuándo llega el primer token y las estadísticas de Ollama.
    """
    cuerpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": pregunta},
        ],
        "stream": True,
        "think": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {"num_predict": MAX_TOKENS_RESPUESTA},
    }
    if metricas:
        metricas.marcar("llm_inicio")
    with ollama_post("/api/chat", cuerpo) as respuesta:
        for linea in respuesta:
            if not linea.strip():
                continue
            dato = json.loads(linea)
            if "error" in dato:
                raise RuntimeError(dato["error"])
            trozo = dato.get("message", {}).get("content", "")
            if trozo:
                if metricas:
                    metricas.marcar("primer_token")
                yield trozo
            if dato.get("done"):
                if metricas:
                    metricas.registrar_ollama(dato)
                break
