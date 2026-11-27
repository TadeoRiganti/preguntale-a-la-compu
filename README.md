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
Si no se entiende la pregunta, suena un tono grave y vuelve a la espera. Para salir, presioná `Ctrl+C` con el asistente en espera.

### Cancelar con Ctrl+C

`Ctrl+C` hace una cosa distinta según lo que esté pasando:

| Situación | Qué hace `Ctrl+C` |
|---|---|
| Esperando la palabra de activación | Cierra el programa |
| Grabando o transcribiendo tu pregunta | Cancela la pregunta y vuelve a esperar la palabra de activación |
| Respondiendo (antes o durante el audio) | Corta el audio y la generación, suena el pitido agudo y queda escuchando una pregunta nueva, sin repetir la palabra de activación |

Si cancelás una respuesta y volvés a apretar `Ctrl+C` mientras te escucha, se cancela esa grabación y vuelve a la espera; a la tercera, cierra el programa.

Kokoro no se puede interrumpir a mitad de una oración: la que estaba sintetizando termina en segundo plano (unos segundos de CPU) y se descarta. Ollama deja de generar cuando termina esa oración, que es cuando el programa le cierra la conexión.
 
## Opciones
 
| Bandera | Descripción | Valor por defecto |
|---|---|---|
| `-m`, `--modelo` | Modelo Whisper para transcribir la pregunta: `base`, `small` o `turbo` | `base` |
| `--ollama` | Modelo de Ollama a utilizar | `gemma4:e4b` |
| `-v`, `--voz` | Voz en español de Kokoro: `ef_dora`, `em_alex`, `em_santa` | `ef_dora` |
| `-p`, `--palabra` | Palabra o frase de activación. Reemplaza a las predeterminadas, vale solo para esa ejecución y se puede repetir. Las frases van entre comillas | `computadora`, `computador`, `compu` |
| `--metricas` | Muestra, después de cada respuesta, cuánto tardó cada etapa | desactivado |
 
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

## Medir la latencia

Con `--metricas` el programa imprime, después de cada respuesta, cuánto tardó cada etapa:

```bash
consultar-computadora --metricas
```

```
⏱️  Espera 3.91s (silencio 1.60s + 1er audio 2.31s) | total 6.80s
    STT 0.80s | 1er token 0.40s | 1ª oración 1.10s | síntesis 1ª oración 0.41s | 18.2 tok/s (86 tokens)
```

Los números son un ejemplo. Qué significa cada uno:

- **Espera:** lo que pasa desde que dejás de hablar hasta que empieza a sonar la respuesta (`silencio` + `1er audio`). Es la latencia que realmente sentís.
- **silencio:** el valor de `SEGUNDOS_SILENCIO`. No se mide: es el tiempo que el asistente espera callado para dar por terminada tu pregunta.
- **1er audio:** desde que terminó la grabación hasta que suena la primera oración (incluye transcripción, Ollama y la síntesis de esa oración).
- **total:** desde que terminó la grabación hasta que termina de hablar.
- **STT:** lo que tardó Whisper en transcribir la pregunta.
- **1er token** y **1ª oración:** lo que tardó Ollama en empezar a responder y en completar la primera oración, medido desde que se le envía la pregunta.
- **síntesis 1ª oración:** lo que tardó Kokoro en generar el primer audio, desde que la primera oración estuvo lista. Si es la parte más grande de la espera, el cuello de botella es la voz y no el modelo de lenguaje.
- **tok/s:** velocidad de generación según Ollama.
- **carga del modelo:** solo aparece si Ollama tuvo que cargar el modelo en memoria (por ejemplo, tras una pausa larga).

Las métricas solo se muestran en la consola; el asistente no las lee en voz alta.
 
## Elegir la palabra de activación

Con `--palabra` (o `-p`) usás otra palabra o frase en lugar de "computadora", solo durante esa ejecución:

```bash
consultar-computadora --palabra tutuca
consultar-computadora --palabra "oye computadora" --palabra tutuca
```

- **Reemplaza a las predeterminadas:** si pasás `--palabra`, ya no activan "computadora", "computador" ni "compu".
- **Las frases van entre comillas**, para que el shell las pase como un solo argumento. En un alias hay que combinar los dos tipos de comillas: `alias asistente='consultar-computadora --palabra "oye computadora"'`.
- **La comparación ignora mayúsculas, tildes y puntuación:** "Oye, computadora." coincide con `oye computadora`.
- **La comparación busca la palabra dentro del texto**, por eso `compu` también activa con "computación". Conviene elegir palabras poco comunes en el habla cotidiana.
- El audio con el que se busca la palabra se corta a 2,2 s (`ACTIVACION_MAX_SEGUNDOS`): una frase larga dicha con calma puede no entrar entera.

## Probar palabras de activación

El subcomando `transcribir` muestra en vivo lo que capta el micrófono, con el mismo audio, modelo (`tiny`) y detección de palabras que usa el asistente mientras espera la palabra. Sirve para ver qué entiende Whisper y por qué se activa (o no), antes de usar una palabra en el asistente:

```bash
consultar-computadora transcribir --palabra tutuca
```

```
[1] 1.8 s de audio · transcripción 0.31s
    Texto: "tutuca."
    ✅ Activaría el asistente: "tutuca" ← tutuca

[2] 2.0 s de audio · transcripción 0.29s
    Texto: "tu tuca"
    ❌ No activaría el asistente

[3] 1.6 s de audio · transcripción 0.27s
    Texto: "tutuka"
    ❌ No activaría el asistente

📊 Resumen: 3 intentos en modo activación
   Activó el asistente: 1 de 3 (33 %)
   Lo que entendió Whisper cuando no activó:
     "tu tuca" ×1
     "tutuka" ×1

👋 Listo.
```

Al salir con `Ctrl+C` muestra cuántas veces activó y qué entendió Whisper cuando no, lo que sirve para decidir si una palabra es confiable. Si no pasás `--palabra`, prueba las palabras predeterminadas. Después de la flecha (`←`) se ven las palabras de activación que coincidieron con cada palabra del texto: el ejemplo `"computación" ← compu` delata un falso positivo.

| Bandera | Descripción | Valor por defecto |
|---|---|---|
| `--modo` | `activacion` (audio corto y modelo liviano, como al esperar la palabra) o `pregunta` (como al grabar la pregunta) | `activacion` |
| `-m`, `--modelo` | Modelo Whisper: `tiny`, `base`, `small` o `turbo` | `tiny` en `activacion`, `base` en `pregunta` |
| `-p`, `--palabra` | Palabra o frase a probar (reemplaza a las predeterminadas; se puede repetir) | las predeterminadas |

Las banderas del asistente (`--ollama`, `--voz`, `--metricas`...) no se aplican a `transcribir`. `--palabra` funciona antes o después del subcomando; `--modo` y `-m` van después de `transcribir` (antes, `-m` sería el modelo Whisper del asistente).

## Ajustes finos
 
Estos valores son constantes al comienzo de cada módulo de `src/consultar_computadora/` (ver la columna Archivo):
 
| Constante | Archivo | Qué controla | Por defecto |
|---|---|---|---|
| `WAKE_WORDS` | `stt.py` | Palabras que activan el asistente (se reemplazan con `--palabra`) | `computadora`, `computador`, `compu` |
| `UMBRAL_SILENCIO` | `audio.py` | Volumen por encima del cual se considera que estás hablando | `0.022` |
| `SEGUNDOS_SILENCIO` | `audio.py` | Segundos de silencio que cierran la grabación de la pregunta | `1.6` |
| `ACTIVACION_MAX_SEGUNDOS` | `audio.py` | Duración máxima del audio con el que se busca la palabra de activación | `2.2` |
| `ACTIVACION_SEGUNDOS_SILENCIO` | `audio.py` | Segundos de silencio que cierran esa grabación | `0.7` |
| `OLLAMA_KEEP_ALIVE` | `llm.py` | Cuánto tiempo queda el modelo de Ollama en memoria tras la última consulta | `30m` |
| `MAX_TOKENS_RESPUESTA` | `llm.py` | Tope de tokens por respuesta (si las respuestas se cortan, subilo) | `300` |
| `MIN_CARACTERES_ORACION` | `tts.py` | Largo mínimo de cada fragmento que se manda al TTS: más bajo empieza a hablar antes, pero suena más entrecortado | `25` |
 
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
- La respuesta solo se puede cancelar con `Ctrl+C`, no con la voz (ver [Pendiente](#pendiente)).
- La detección de la palabra de activación se basa en transcripción, por lo que a veces puede fallar o dar falsos positivos.
- Es un proyecto vibecodeado: puede tener errores y no tiene tests automáticos.
## Pendiente

- **Cancelar por voz** (una palabra o la propia palabra de activación como interrupción). Queda para cuando se reemplace Kokoro por Piper, junto con una captura de audio que siga escuchando mientras el asistente habla. Habría que resolver antes tres cosas: el eco (los parlantes entran al micrófono y Whisper transcribiría la propia respuesta; con auriculares o cancelación de eco se evita), el costo de CPU de transcribir en continuo mientras se sintetiza, y la demora de ~1 s hasta que se confirma la palabra.

## Estructura del proyecto
 
```
.
├── install.sh                      # Instalador (dependencias del sistema + uv + comando global)
├── pyproject.toml                  # Metadatos y dependencias del paquete
└── src/consultar_computadora/
    ├── audio.py                    # Captura del micrófono, detección de silencio y tono de confirmación
    ├── cli.py                      # Orquestador: argumentos y bucle principal
    ├── llm.py                      # Cliente de la API local de Ollama (streaming)
    ├── metricas.py                 # Cronómetro opcional (--metricas)
    ├── stt.py                      # Transcripción con Whisper y palabras de activación
    ├── transcribir.py              # Subcomando de depuración: transcribir
    └── tts.py                      # Corte en oraciones y reproducción con Kokoro
```
 
## Tecnologías
 
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): reconocimiento de voz
- [Ollama](https://ollama.com): ejecución local del modelo de lenguaje
- [Kokoro TTS](https://github.com/hexgrad/kokoro): síntesis de voz
- [sounddevice](https://python-sounddevice.readthedocs.io/): captura y reproducción de audio
- [uv](https://docs.astral.sh/uv/): gestión de paquetes e instalación
## Licencia
 
Este repositorio todavía no tiene una licencia definida. Si querés que otras personas puedan usarlo y modificarlo, agregá un archivo `LICENSE` (por ejemplo, MIT).
 

