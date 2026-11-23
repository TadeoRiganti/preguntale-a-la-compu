# Preguntale a la compu 🎙️🤖
 
[![Built with Gemma](https://vibecoded.fyi/badges/flat/llms/gemma.svg)](https://vibecoded.fyi/)
 
Asistente de voz continuo y **100% local** en español para Linux/Ubuntu. Lo activás diciendo **"Computadora"**, le hacés tu pregunta en voz alta y te responde hablando. Todo corre en tu máquina: sin APIs, sin cuentas y sin enviar tu voz a ninguna nube.
 
> **Nota:** Este proyecto está **99% vibecodeado** (creado y depurado mediante iteraciones conversacionales con IA). Es un proyecto personal y experimental: usalo con ese criterio.
 
## Cómo funciona
 
```
Micrófono ──► Whisper tiny (detecta "Computadora")
                  │
                  ▼  pitido de confirmación
Micrófono ──► Whisper base/small/turbo (transcribe tu pregunta)
                  │
                  ▼
              Ollama (genera la respuesta)
                  │
                  ▼
              Kokoro TTS (la lee en voz alta) ──► Parlantes
```
 
1. El programa escucha en bucle fragmentos cortos de audio y los transcribe con un modelo Whisper liviano (`tiny`) buscando la palabra de activación.
2. Al detectarla, emite un pitido y graba tu pregunta hasta que haces una pausa de silencio.
3. La pregunta se transcribe con el modelo Whisper que elijas (`base` por defecto).
4. Se la envía a un modelo local de [Ollama](https://ollama.com) por su API local, con la instrucción de responder en español, en texto plano y de forma concisa. La respuesta llega en streaming.
5. [Kokoro TTS](https://github.com/hexgrad/kokoro) la lee en voz alta oración por oración, a medida que llega (mientras reproduce una oración ya sintetiza la siguiente), y el asistente vuelve a quedar en espera.
## Requisitos
 
| Requisito | Detalle |
|---|---|
| Sistema operativo | Linux basado en Debian/Ubuntu (el instalador usa `apt-get`) |
| Python | 3.11 o 3.12 (el proyecto declara `>=3.11,<3.13`) |
| Micrófono y parlantes | Dispositivos de audio de entrada y salida funcionando |
| [Ollama](https://ollama.com) | Instalado y con el servicio corriendo (el programa lo consulta por su API local) |
| Modelo de Ollama | Por defecto `gemma4:e4b` (ver más abajo) |
| Internet | Solo en la primera ejecución, para descargar los modelos |
| Hardware | Funciona en CPU (PyTorch CPU y Whisper en `int8`). Una GPU no es necesaria para Whisper/Kokoro, pero el tiempo de respuesta depende mucho del modelo de Ollama y de tu equipo |
 
Paquetes del sistema que instala `install.sh`: `espeak-ng` (lo usa Kokoro para fonética), `libportaudio2` (captura y reproducción de audio) y `curl`.
 
## Instalación
 
### 1. Instalar y preparar Ollama
 
Seguí las instrucciones oficiales en [ollama.com](https://ollama.com) y después descargá el modelo por defecto:
 
```bash
ollama pull gemma4:e4b
```
 
Podés usar cualquier otro modelo que tengas disponible (ver [Opciones](#opciones)). Tené en cuenta que el programa consulta a Ollama por su API local (por defecto en `http://127.0.0.1:11434`, o la que indique `OLLAMA_HOST`) y le pide que no use modo de razonamiento (`think: false`), así que conviene tener una versión reciente de Ollama.
 
### 2. Clonar e instalar
 
```bash
git clone https://github.com/TadeoRiganti/preguntale-a-la-compu.git
cd preguntale-a-la-compu
./install.sh
```
 
El script:
 
1. Instala `espeak-ng`, `libportaudio2` y `curl` con `sudo apt-get` (te va a pedir la contraseña).
2. Instala [`uv`](https://docs.astral.sh/uv/) si no lo tenés.
3. Instala el comando global `consultar-computadora` con `uv tool install --force .`.
> Si `consultar-computadora` no aparece en tu terminal después de instalar, abrí una terminal nueva o agregá `~/.local/bin` a tu `PATH`.
 
### Instalación manual (alternativa)
 
```bash
sudo apt-get install -y espeak-ng libportaudio2
uv tool install --force .
```
 
## Uso
 
```bash
consultar-computadora
```
 
La primera vez descarga los modelos de Whisper y Kokoro (puede tardar unos minutos). Cuando veas el mensaje de que la computadora está activa:
 
1. Decí **"Computadora"** (también funcionan "computador" y "compu").
2. Esperá el pitido agudo y hacé tu pregunta.
3. Hacé una pausa de ~1,6 segundos: el asistente interpreta el silencio como fin de la pregunta.
4. Escuchá la respuesta. Cuando termina, vuelve a esperar la palabra de activación.
Si no se entiende la pregunta, suena un tono grave y vuelve a la espera. Para salir, presioná `Ctrl+C`.
 
## Opciones
 
| Bandera | Descripción | Valor por defecto |
|---|---|---|
| `-m`, `--modelo` | Modelo Whisper para transcribir la pregunta: `base`, `small` o `turbo` | `base` |
| `--ollama` | Modelo de Ollama a utilizar | `gemma4:e4b` |
| `-v`, `--voz` | Voz en español de Kokoro: `ef_dora`, `em_alex`, `em_santa` | `ef_dora` |
 
Ejemplos:
 
```bash
# Mejor transcripción, un poco más lento
consultar-computadora --modelo small
 
# Otro modelo de Ollama y voz masculina
consultar-computadora --ollama llama3.2 --voz em_alex
 
# Máxima precisión de transcripción
consultar-computadora -m turbo -v ef_dora
```
 
Elegir el modelo Whisper es un compromiso entre velocidad y precisión: `base` es el más rápido, `small` equilibra ambos y `turbo` es el más preciso pero el que más recursos consume.
 
## Ajustes finos
 
Estos valores están al comienzo de `src/consultar_computadora/cli.py`:
 
| Constante | Qué controla | Por defecto |
|---|---|---|
| `WAKE_WORDS` | Palabras que activan el asistente | `computadora`, `computador`, `compu` |
| `UMBRAL_SILENCIO` | Volumen por encima del cual se considera que estás hablando | `0.022` |
| `SEGUNDOS_SILENCIO` | Segundos de silencio que cierran la grabación de la pregunta | `1.6` |
| `OLLAMA_KEEP_ALIVE` | Cuánto tiempo queda el modelo de Ollama en memoria tras la última consulta | `30m` |
| `MAX_TOKENS_RESPUESTA` | Tope de tokens por respuesta (si las respuestas se cortan, subilo) | `300` |
| `MIN_CARACTERES_ORACION` | Largo mínimo de cada fragmento que se manda al TTS: más bajo empieza a hablar antes, pero suena más entrecortado | `25` |
 
Si instalaste con `uv tool install`, después de editar el código volvé a ejecutar `uv tool install --force .` para que el comando global use tus cambios.
 
## Privacidad
 
- La voz se transcribe localmente con Whisper y la respuesta se genera localmente con Ollama; el audio y las preguntas no salen de tu equipo.
- Internet solo se usa para descargar los modelos la primera vez (Whisper y Kokoro desde Hugging Face, y el modelo de Ollama con `ollama pull`). Después podés usarlo sin conexión.
- El micrófono permanece escuchando mientras el programa está abierto, pero solo se procesa el audio localmente y no se guarda ninguna grabación.
## Solución de problemas
 
**`Error: no se pudo conectar con Ollama`**
Instalá Ollama y comprobá que el servicio esté corriendo (por defecto escucha en el puerto 11434). Si lo corrés en otro host o puerto, definí la variable `OLLAMA_HOST`.
 
**La respuesta aparece vacía o falla la consulta**
Verificá que el servicio de Ollama esté corriendo y que hayas descargado el modelo con `ollama pull <modelo>`. Probá también ejecutar a mano `ollama run <modelo> "hola"`. Si tu versión de Ollama es vieja y no reconoce el parámetro `think`, actualizala.
 
**No detecta "Computadora" o se activa sin querer**
Hablá cerca del micrófono, con poco ruido de fondo. Ajustá `UMBRAL_SILENCIO` si el micrófono tiene muy poco o demasiado volumen de entrada.
 
**Corta la pregunta antes de que termine**
Aumentá `SEGUNDOS_SILENCIO` si hacés pausas largas mientras hablás.
 
**No se escucha el audio o no capta el micrófono**
Confirmá que `libportaudio2` esté instalado y que el micrófono y los parlantes predeterminados del sistema sean los correctos (por ejemplo, desde la configuración de sonido del escritorio).
 
**Errores de Kokoro relacionados con `espeak`**
Instalá `espeak-ng` con `sudo apt-get install espeak-ng`.
 
**Es muy lento**
Probá un modelo más chico en `--ollama` y mantené el modelo Whisper en `base`. La transcripción corre en CPU.
 
## Limitaciones conocidas
 
- Solo Linux (probado con Ubuntu/Debian); el instalador depende de `apt-get`.
- No tiene memoria de conversación: cada pregunta se responde de forma independiente.
- No se puede interrumpir la respuesta mientras el asistente habla.
- La detección de la palabra de activación se basa en transcripción, por lo que a veces puede fallar o dar falsos positivos.
- Es un proyecto vibecodeado: puede tener errores y no tiene tests automáticos.
## Estructura del proyecto
 
```
.
├── install.sh                      # Instalador (dependencias del sistema + uv + comando global)
├── pyproject.toml                  # Metadatos y dependencias del paquete
└── src/consultar_computadora/
    └── cli.py                      # Toda la lógica del asistente
```
 
## Tecnologías
 
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): reconocimiento de voz
- [Ollama](https://ollama.com): ejecución local del modelo de lenguaje
- [Kokoro TTS](https://github.com/hexgrad/kokoro): síntesis de voz
- [sounddevice](https://python-sounddevice.readthedocs.io/): captura y reproducción de audio
- [uv](https://docs.astral.sh/uv/): gestión de paquetes e instalación
## Licencia
 
Este repositorio todavía no tiene una licencia definida. Si querés que otras personas puedan usarlo y modificarlo, agregá un archivo `LICENSE` (por ejemplo, MIT).
 

