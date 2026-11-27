# 🎙️ Asistente de Voz Local
### Especificación técnica y hoja de ruta

---

# 1. Propósito y Alcance del Proyecto

## 1.1. Propósito

Desarrollar un asistente de voz local como proyecto de aprendizaje y experimentación con Inteligencia Artificial, Python y desarrollo asistido por IA (vibecoding).

El proyecto tiene dos objetivos complementarios:

**Objetivo funcional:** construir un asistente de voz autónomo, modular, liviano y de baja latencia, capaz de escuchar consultas puntuales, procesarlas mediante un modelo de lenguaje local y responder utilizando voz, sin depender de servicios en la nube.

**Objetivo de aprendizaje:** adquirir experiencia práctica en integración de modelos locales, procesamiento de audio, arquitectura modular, optimización de recursos, comunicación entre servicios y desarrollo asistido por IA.

Este proyecto constituye una experiencia preparatoria para futuros desarrollos de domótica basados en Home Assistant. No pretende reemplazar sus funcionalidades ni reinventar sus soluciones, sino familiarizarme con las tecnologías y los conceptos necesarios para personalizar, integrar y ampliar un ecosistema domótico propio.

## 1.2. Alcance funcional

El asistente debe poder:

1. Capturar consultas mediante un micrófono.
2. Detectar cuándo el usuario terminó de hablar.
3. Transcribir el audio a texto.
4. Procesar la consulta utilizando un LLM local.
5. Generar una respuesta breve y concisa.
6. Convertir la respuesta en voz.
7. Reproducirla progresivamente, minimizando la latencia percibida.

El funcionamiento será **stateless**: cada consulta se procesa de manera independiente, sin conservar memoria conversacional ni historial de interacciones.

## 1.3. Límites del proyecto

El desarrollo se mantiene deliberadamente enfocado en el asistente de consultas por voz.

Quedan fuera del alcance de esta etapa:

- Control de dispositivos domóticos.
- Automatizaciones del hogar.
- Integración directa con Home Assistant.
- Memoria conversacional o gestión de contexto entre consultas.
- Dependencias de servicios externos o APIs en la nube.

Estas funcionalidades podrán considerarse en proyectos posteriores, una vez adquirida la experiencia necesaria.

---

# 2. Objetivo Técnico y Restricciones

Desarrollar una aplicación en Python, 100 % local, modular y de baja latencia.

### Restricciones de hardware

**Entorno de desarrollo:**
- PC de escritorio.
- Ryzen 5 2600.
- 64 GB RAM.
- 12 GB VRAM.

**Entorno objetivo primario:**
- Laptop sin GPU dedicada.
- 8 GB RAM totales.
- Aproximadamente 4.5 GB disponibles para la aplicación.

**Entorno objetivo futuro:**
- Mini PC / Raspberry Pi 4 o 5.
- Arquitectura ARM64.
- 4-8 GB RAM.

### Reglas de oro

- Cero dependencias pesadas innecesarias (no PyTorch).
- Cero archivos temporales `.wav` en disco.
- Procesamiento de audio directamente en memoria.
- Carga única de modelos al iniciar la aplicación.
- Arquitectura modular: cada componente debe poder probarse y reemplazarse independientemente.
- Adaptación de recursos según el hardware disponible.

---

# 3. Stack Tecnológico y Arquitectura

## 3.1. Pipeline de datos

El flujo principal de procesamiento será:

`[Micrófono + VAD]` ➔ `Faster-Whisper (STT)` ➔ `llama.cpp Stream (LLM)` ➔ `Segmentador por Oraciones` ➔ `Piper TTS` ➔ `[Altavoz]`

El procesamiento debe realizarse íntegramente en memoria, evitando archivos temporales y transferencias innecesarias.

## 3.2. Estructura de archivos

```text
asistente_voz/
├── ASISTENTE_VOZ_LOCAL_SPEC.md  # Documento maestro del proyecto
├── config.py                   # Perfiles de hardware
├── main.py                     # Orquestador del bucle principal
├── audio_in.py                 # Captura de micrófono y VAD
├── stt.py                      # Reconocimiento de voz
├── llm.py                      # Motor LLM
├── tts.py                      # Síntesis y reproducción de voz
├── modelos/                    # Modelos locales
│   ├── llm/
│   └── tts/
└── requirements.txt             # Dependencias exactas
```

---

# 4. Reglas de Implementación por Módulo

## 4.1. `config.py` — Perfiles Adaptativos

Centralizar rutas de archivos y recursos mediante una variable `PERFIL_ACTIVO`.

**PC_GPU:**
- Whisper: `medium` (`cuda`, `float16`).
- LLM: `Qwen2.5-7B-Instruct-Q4_K_M.gguf`.
- `n_gpu_layers=-1`.
- `n_ctx=2048`.

**LAPTOP_8GB:**
- Whisper: `base` (`cpu`, `int8`, `cpu_threads=4`).
- LLM: `Qwen2.5-3B-Instruct-Q4_K_M.gguf`.
- `n_gpu_layers=0`.
- `n_ctx=512`.
- `n_threads=4`.

**RASPBERRY:**
- Whisper: `tiny` (`cpu`, `int8`, `cpu_threads=4`).
- LLM: `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf`.
- `n_gpu_layers=0`.
- `n_ctx=512`.
- `n_threads=4`.

## 4.2. `audio_in.py` — Entrada de Audio

- Utilizar `sounddevice`.
- Captura a 16 kHz, mono, `int16`.
- Implementar detección de silencio y finalización de consulta.
- Utilizar VAD liviano (`webrtcvad`) o umbral RMS con ventana de silencio de aproximadamente 1.2 segundos.

**Opcional — Fase 2:**
- Activación por Wake Word mediante `openwakeword`.
- Alternativamente, tecla Push-to-Talk (PTT) durante la primera fase.

## 4.3. `stt.py` — Speech-to-Text

Librería: `faster-whisper`.

- Cargar `WhisperModel` una sola vez al inicializar el módulo.
- Forzar `language="es"`.
- Utilizar `beam_size=1` para priorizar velocidad en CPU.
- Evitar conversiones y escrituras innecesarias en disco.

## 4.4. `llm.py` — Motor de Lenguaje

Librería definitiva: `llama-cpp-python`.

**Prototipado:**
Puede utilizarse Ollama temporalmente para experimentar con modelos y prompts.

**Implementación definitiva:**
- Cargar directamente modelos locales `.gguf`.
- Preferir cuantizaciones `Q4_K_M` o `Q4_0` para ARM.
- Cargar el objeto `Llama(...)` una sola vez al iniciar.
- Utilizar `verbose=False` y `use_mmap=True`.
- Implementar generación mediante `create_chat_completion(..., stream=True)`.

**Procesamiento stateless:**

Enviar únicamente el mensaje de sistema y la consulta actual, sin almacenar historial conversacional.

**System Prompt obligatorio:**

"Eres un asistente de voz conciso y directo. Responde únicamente en texto plano en español. Prohibido usar markdown, asteriscos, listas, viñetas, emojis o bloques de código."

**Streaming por oraciones:**

Acumular tokens en un buffer y entregar el texto mediante `yield` apenas se detecte un delimitador de oración (`.`, `!`, `?`, `\n`).

El objetivo es alimentar al módulo TTS antes de que el LLM termine de generar toda la respuesta.

## 4.5. `tts.py` — Text-to-Speech

Librerías:
- `piper-tts`.
- `sounddevice`.
- `numpy`.

**Implementación:**
- Cargar el modelo `.onnx` una sola vez en memoria.
- Modelo de referencia: `es_ES-davefx-medium.onnx`.
- Utilizar `PiperVoice.load`.
- Implementar reproducción mediante `sounddevice.OutputStream`.
- Enviar los chunks de audio `int16` directamente al dispositivo de salida.
- Utilizar `synthesize_stream_raw()` para evitar la generación de archivos `.wav`.

---

# 5. Hoja de Ruta de Desarrollo

El desarrollo se realizará de manera incremental, probando cada módulo de forma independiente antes de integrarlo.

La prioridad es conseguir componentes funcionales y medibles antes de avanzar hacia el siguiente paso.

### Paso 1 — Esqueleto y Descarga de Modelos

- [ ] Crear estructura de carpetas.
- [ ] Implementar `config.py`.
- [ ] Definir perfiles de hardware.
- [ ] Descargar modelos `.onnx` (Piper).
- [ ] Descargar modelo `.gguf` (`Qwen2.5-3B-Instruct-Q4_K_M.gguf`).

### Paso 2 — Módulo de Voz (`tts.py`)

- [ ] Implementar carga única del modelo Piper.
- [ ] Implementar reproducción mediante streaming.
- [ ] Probar generación y reproducción con texto fijo.
- [ ] Verificar que no se generen archivos temporales.

### Paso 3 — Módulo de Lenguaje (`llm.py`)

- [ ] Implementar carga del modelo GGUF mediante `llama-cpp-python`.
- [ ] Implementar generación de texto en streaming.
- [ ] Implementar segmentador por oraciones.
- [ ] Conectar la salida del LLM con `tts.py`.
- [ ] Medir tiempo hasta el primer token y primera reproducción.

### Paso 4 — Módulo de Escucha (`audio_in.py` + `stt.py`)

- [ ] Implementar captura de micrófono.
- [ ] Implementar detección de actividad de voz (VAD).
- [ ] Implementar corte automático por silencio.
- [ ] Integrar transcripción mediante Faster-Whisper.
- [ ] Probar consultas de forma independiente.

### Paso 5 — Integración (`main.py`)

- [ ] Unificar los módulos en el bucle principal.
- [ ] Implementar el ciclo completo de escucha, procesamiento y respuesta.
- [ ] Verificar que las consultas sean independientes.
- [ ] Incorporar métricas de rendimiento:
  - Tiempo de transcripción (STT).
  - Tiempo hasta el primer token (LLM).
  - Tiempo hasta la primera oración.
  - Tiempo de síntesis y reproducción (TTS).
  - Latencia total percibida.

### Paso 6 — Simulación de Restricciones (`LAPTOP_8GB`)

- [ ] Ejecutar el modelo LLM forzando `n_gpu_layers=0`.
- [ ] Ejecutar Whisper utilizando `device="cpu"`.
- [ ] Medir consumo real de RAM mediante `psutil`.
- [ ] Medir latencia de cada componente.
- [ ] Detectar cuellos de botella.
- [ ] Evaluar si el sistema puede funcionar dentro del presupuesto disponible de memoria.

---

# 6. Criterios de Finalización

El proyecto se considerará funcionalmente terminado cuando:

- El asistente pueda escuchar y responder consultas por voz de principio a fin.
- Todo el procesamiento se realice localmente.
- No se generen archivos temporales de audio.
- Los modelos se carguen una sola vez al iniciar.
- La respuesta pueda reproducirse progresivamente.
- Las consultas se procesen de manera independiente.
- El sistema pueda ejecutarse en el hardware objetivo primario (LAPTOP_8GB).
- Se disponga de métricas básicas para evaluar rendimiento y consumo de recursos.

---

# 7. Consideraciones para el Desarrollo Asistido por IA

Este proyecto se desarrolla utilizando herramientas de IA como apoyo para escribir, refactorizar, documentar y optimizar código.

Sin embargo, las decisiones de arquitectura y los cambios importantes deben comprenderse y validarse antes de incorporarse.

**Reglas de trabajo:**

1. Respetar el alcance definido en este documento.
2. No incorporar funcionalidades que no estén contempladas en la hoja de ruta sin evaluar previamente su necesidad.
3. Priorizar soluciones livianas y compatibles con el hardware objetivo.
4. Mantener la arquitectura modular y evitar acoplamientos innecesarios.
5. No reemplazar tecnologías o dependencias sin justificar las ventajas y desventajas.
6. No introducir dependencias adicionales sin explicar su propósito y costo.
7. Probar cada módulo de manera independiente antes de integrarlo.
8. Documentar cambios importantes en la arquitectura y las decisiones técnicas.
9. Evitar reescrituras completas cuando una refactorización localizada sea suficiente.
10. Ante decisiones técnicas relevantes, presentar alternativas y sus consecuencias antes de modificar la implementación.

**Principio rector:** el objetivo no es simplemente conseguir que el código funcione, sino construir una solución comprensible, mantenible y optimizada, aprovechando el desarrollo asistido por IA como herramienta de aprendizaje.
