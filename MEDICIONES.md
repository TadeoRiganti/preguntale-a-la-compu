# Mediciones y pruebas de control

Registro para comparar la latencia y comprobar que nada se rompa entre versiones.

## Cómo medir

1. Cerrar los programas que consuman mucha CPU o GPU.
2. Ejecutar `consultar-computadora --metricas`.
3. Hacer las tres preguntas de control, en este orden:
   1. «¿Por qué el cielo es azul?»
   2. «¿Cómo funciona un panel solar? ¿Cómo transforma la radiación solar en energía eléctrica?»
   3. «¿De qué color es el caballo blanco de San Martín?»
4. Anotar los valores en una sección nueva, con la fecha, el commit (`git rev-parse --short HEAD`), el equipo y las opciones usadas.

La respuesta del modelo cambia entre ejecuciones, así que también cambia el largo de la primera oración. Para comparar la síntesis conviene mirar los milisegundos por carácter.

## Resultados

### Línea base con Kokoro

- **Fecha:** 2026-11-27
- **Versión:** `v0.1.0-kokoro` (`61f7fe5`)
- **Equipo:** PC de escritorio (Ryzen 5 2600, 64 GB de RAM, GPU de 12 GB)
- **Opciones:** predeterminadas (Whisper `base`, Ollama `gemma4:e4b`, voz `ef_dora`)
- **Muestras:** una por pregunta

Tiempos en segundos. La espera incluye 1,60 s de silencio.

| Pregunta | Espera | 1er audio | STT | 1er token | 1ª oración | Síntesis 1ª oración | Total | tok/s (tokens) |
|---|---|---|---|---|---|---|---|---|
| 1. Cielo | 6,59 | 4,99 | 0,97 | 0,69 | 0,96 | 3,06 | 45,95 | 61,9 (139) |
| 2. Panel solar | 6,78 | 5,18 | 1,02 | 0,54 | 0,83 | 3,33 | 89,49 | 62,2 (289) |
| 3. Caballo | 4,54 | 2,94 | 0,96 | 0,65 | 0,78 | 1,19 | 5,98 | 72,6 (10) |

Síntesis según el largo de la primera oración:

| Pregunta | Primera oración | Caracteres | Síntesis | ms por carácter |
|---|---|---|---|---|
| 1 | «El cielo se ve azul debido a un fenómeno llamado dispersión de Rayleigh.» | 72 | 3,06 s | 42 |
| 2 | «Un panel solar, o panel fotovoltaico, funciona aprovechando el efecto fotovoltaico.» | 83 | 3,33 s | 40 |
| 3 | «El caballo blanco de San Martín es blanco.» | 42 | 1,19 s | 28 |

## Pruebas funcionales

Repasar después de cada cambio importante:

- [ ] Se activa con «computadora» y suena el pitido.
- [ ] Responde en voz alta, sin cortes ni palabras mal pronunciadas que impidan entender.
- [ ] `Ctrl+C` durante la respuesta corta el audio y queda escuchando otra pregunta.
- [ ] `Ctrl+C` durante la pregunta la cancela y repite las instrucciones.
- [ ] `Ctrl+C` en espera cierra el programa.
- [ ] Una activación sin pregunta no rompe el bucle.
- [ ] `--voz`, `--palabra` y `--metricas` funcionan.
- [ ] `consultar-computadora transcribir` funciona.
- [ ] Funciona sin conexión a internet después de la primera ejecución.
