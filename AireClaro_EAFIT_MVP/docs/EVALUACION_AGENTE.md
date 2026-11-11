# Evaluación manual del agente (15 preguntas)

Completa esta tabla después de ejecutar la app. No marques “Pasa” antes de comprobar la respuesta. En modo sin API, revisa el flujo local y el nombre de la herramienta mostrado bajo la respuesta. Con Groq, verifica también la salida del modelo; una llamada se considera correcta solo si la herramienta corresponde a la intención de la pregunta y los datos citados coinciden con el panel/CSV.

| # | Pregunta de prueba | Herramienta esperada | Criterio para aprobar | Resultado / captura |
|---:|---|---|---|---|
| 1 | ¿Cuál es la última lectura de la estación seleccionada? | `get_pm25` | Devuelve concentración, categoría y hora SIATA; aclara promedio 24 h | [pendiente] |
| 2 | ¿Qué PM2.5 tiene la estación seleccionada? | `get_pm25` | Coincide con el panel, código y actualización | [pendiente] |
| 3 | Consulta la concentración de la estación seleccionada | `get_pm25` | No la llama lectura instantánea | [pendiente] |
| 4 | ¿Cuál es la categoría publicada por SIATA? | `get_pm25` | Usa la categoría de la capa y la fuente oficial | [pendiente] |
| 5 | ¿De qué hora es esta medición? | `get_pm25` | Indica timestamp y periodo promedio 24 h | [pendiente] |
| 6 | ¿Qué estación está seleccionada? | `get_pm25` | Devuelve código SIATA y municipio del selector | [pendiente] |
| 7 | ¿De dónde sale el valor que muestra el panel? | `get_pm25` / `search_docs` | Cita el geoportal SIATA, no Groq como fuente de datos | [pendiente] |
| 8 | ¿Qué categoría habrá mañana según los datos de SIATA? | `predict_tomorrow` | Indica que no predice porque la capa solo entrega promedios 24 h | [pendiente] |
| 9 | Predice mañana y explícame qué tan bien funciona | `predict_tomorrow` | No presenta el modelo simulado como pronóstico real | [pendiente] |
| 10 | En modo Demo, compara la predicción con la línea base | `predict_tomorrow` | Cambia explícitamente a Demo y muestra ambas métricas simuladas | [pendiente] |
| 11 | ¿Qué información ofrece el conjunto de datos del IDEAM? | `search_docs` | Recupera la ficha IDEAM y su URL | [pendiente] |
| 12 | Busca el contexto del informe de SIATA | `search_docs` | Recupera el documento local SIATA | [pendiente] |
| 13 | ¿Qué fuentes de información tiene este proyecto? | `search_docs` | Cita documentos del corpus; no inventa mediciones | [pendiente] |
| 14 | ¿Qué información contiene el documento de SIATA? | `search_docs` | Recupera el documento local SIATA y muestra su fuente | [pendiente] |
| 15 | ¿Es una lectura instantánea en tiempo real? | `get_pm25` | Aclara que es promedio móvil de 24 h y muestra hora de actualización | [pendiente] |

**Fecha de ejecución:** [completar] · **Modo usado:** local / Groq · **CSV y procedencia:** [completar] · **Ejecutor:** [completar]

Usa los nombres de capturas sugeridos en `evidencias/INSTRUCCIONES_CAPTURAS.md` y enlázalos en la columna final. Estas preguntas son una plantilla; anota cualquier respuesta incorrecta y la corrección aplicada.
