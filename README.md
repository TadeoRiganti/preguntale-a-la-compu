# Consultar Computadora 🎙️🤖

Asistente de voz continuo y 100% local en español para Linux/Ubuntu. Escucha en segundo plano la palabra clave **"Computadora"**, transcribe tu consulta con **Whisper**, la procesa con **Ollama** y responde en voz alta usando **Kokoro TTS**.

## Requisitos previos
- Linux (Ubuntu / Debian) con micrófono y salida de audio.
- [Ollama](https://ollama.com) instalado con el modelo descargado (`ollama pull gemma4:e4b`).

## Instalación rápida

```bash
git clone https://github.com
cd consultar-computadora
./install.sh
```

## Uso

Ejecuta el comando desde cualquier terminal:

```bash
consultar-computadora
```

Di **"Computadora"**, espera el pitido de confirmación y haz tu pregunta. Presiona `Ctrl + C` para apagar el micrófono y salir.

### Opciones disponibles
- `-m {base,small,turbo}`: Cambia la precisión del modelo Whisper (por defecto: `base`).
- `--ollama MODELO`: Usa otro modelo de Ollama (por defecto: `gemma4:e4b`).
- `-v {ef_dora,em_alex,em_santa}`: Cambia la voz en español de Kokoro (por defecto: `ef_dora`).

Ejemplo:
```bash
consultar-computadora -m small --ollama llama3.2 -v em_alex
```
