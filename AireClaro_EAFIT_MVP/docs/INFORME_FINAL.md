# AireClaro: asistente educativo de calidad del aire

**Curso:** SI3003 Inteligencia Artificial · **Equipo:** [completar] · **Integrantes:** [completar]

## Problema y objetivo

El proyecto ofrece un panel de PM2.5 por estación del Valle de Aburrá y un chat que consulta observaciones, recupera fuentes y explica los límites de pronóstico. SIATA es la fuente ambiental de las observaciones en vivo; Groq, cuando se configura, es el modelo de lenguaje que redacta respuestas y decide cuándo invocar herramientas.

## Fuente de datos y preparación

El modo predeterminado consulta las capas públicas ICA PM2.5 POECA y NO-POECA del [geoportal SIATA](https://siata.gov.co/siata_nuevo/), mediante el servicio de consulta de capas del geoportal. La app lee estación, municipio, concentración, categoría oficial de la capa y fecha/hora de actualización. SIATA publica promedios móviles de 24 horas por estación; no son mediciones instantáneas ([descripción GeoSAT](https://geosat.com.co/es/mapas/medellin/ambiente)). La respuesta conserva la fecha y aclara ese periodo. Las consultas se cachean cinco minutos. Si el servicio falla, el panel informa y usa el CSV de demostración, que contiene 210 registros sintéticos y no representa condiciones actuales.

Para entrenamiento o evaluación predictiva reproducible se puede cargar un CSV histórico con `fecha, estacion, municipio, pm25` (coordenadas opcionales). El equipo debe adjuntar la fuente, fecha de descarga, unidad y transformaciones. Las capas recientes de SIATA no aportan historia suficiente para validar una predicción de mañana.

## Método clásico y evaluación

`app.py` implementa un Naive Bayes gaussiano de una variable y compara su exactitud con una línea base de clase mayoritaria usando una partición cronológica 80/20. El resultado mostrado se calcula con el CSV seleccionado y es educativo; con el conjunto simulado incluido se comprueba el flujo de punta a punta. No reportar esas métricas como rendimiento ambiental real. En modo SIATA, la app desactiva el pronóstico porque una lectura agregada de 24 h por estación no constituye una serie histórica de entrenamiento.

## Agente, RAG e interfaz

El agente utiliza Groq opcionalmente y dispone de `get_pm25`, `predict_tomorrow` y `search_docs`. `get_pm25` consulta el conjunto activo (SIATA en modo real); `search_docs` busca extractos en `knowledge/`; `predict_tomorrow` explica la limitación al usar la capa SIATA y demuestra el clasificador solo con datos históricos/demo. La integración local no envía la clave en la interfaz ni la guarda en el repositorio. El modo sin Groq ofrece respuestas deterministas. El corpus RAG es pequeño y su recuperación es por coincidencia de términos.

## Resultados, límites y próximos pasos

Las pruebas automatizadas cubren arranque, predicción demo y búsqueda local. Antes de entregar, ejecutar las preguntas manuales de `docs/EVALUACION_AGENTE.md`, guardar evidencias en `evidencias/`, completar nombres del equipo y verificar la vigencia/disponibilidad del servicio SIATA. La conexión es un servicio público sujeto a disponibilidad. Las categorías propias del CSV son didácticas y no son alertas oficiales ni consejo médico. No usar la aplicación para decisiones de salud pública.

## Uso de IA generativa

La declaración detallada está en `docs/DECLARACION_USO_IA.md`. Completarla con los nombres, fecha y revisión del equipo antes de entregar.
