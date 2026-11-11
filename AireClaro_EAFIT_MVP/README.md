# AireClaro — proyecto final SI3003

**Fecha límite indicada en la guía del curso:** viernes 13 de noviembre de 2026, 6:00 p. m.

Dashboard y chat para explorar calidad del aire en el Valle de Aburrá. Esta carpeta contiene el código, datos de demostración, corpus local, pruebas, informe, declaración de uso de IA y guía para tomar evidencias.

> **Fuente real:** por defecto, la app consulta las capas públicas ICA PM2.5 de SIATA (POECA y NO-POECA). Las lecturas son promedios móviles de 24 horas por estación, con hora de actualización y categoría publicadas. Groq genera el texto del chat, pero no proporciona los datos ambientales. Si SIATA no está disponible, la interfaz avisa y cambia al CSV simulado. Las métricas de clasificación y predicción siguen siendo demostrativas: las capas actuales no dan suficiente historial para validar un pronóstico.

## 1. Requisitos

- Windows 10/11 y Python 3.10 o superior.
- Conexión a internet para consultar SIATA y, si se configura, Groq.
- Para activar el chat con Groq: una clave vigente guardada únicamente en `.env` local. No subas ese archivo.

## 2. Instalación y ejecución paso a paso

Abre PowerShell y ejecuta cada línea:

```powershell
cd "$HOME\OneDrive\Desktop\IA\AireClaro_EAFIT_MVP"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit mostrará una URL local, normalmente **http://localhost:8501**. Ábrela en Chrome o Edge. Deja abierta la ventana de PowerShell mientras usas la app; `Ctrl+C` detiene el servidor.

Si PowerShell no permite activar el entorno, no cambies la política del equipo: ejecuta los comandos del entorno de forma directa:

```powershell
cd "$HOME\OneDrive\Desktop\IA\AireClaro_EAFIT_MVP"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

También se puede iniciar `iniciar_demo.ps1` desde la carpeta. El comando explícito de arriba es el procedimiento principal y deja visible la salida de Streamlit.

## 3. Probar la app a mano

1. En la barra lateral deja **SIATA · mediciones recientes** seleccionado. Comprueba el indicador de conexión, hora y estaciones. La lectura es promedio móvil de 24 horas, no instantánea.
2. Revisa las métricas y gráficas y selecciona una estación SIATA.
3. Pregunta “¿Cuál es el PM2.5 y la categoría publicados para esta estación?”; `get_pm25` recupera la observación SIATA.
4. Pregunta “¿Qué recomendaciones aparecen en las fuentes?”; `search_docs` recupera contexto documental.
5. Pulsa **Probar predicción**. SIATA no ofrece historia apta para pronosticar mañana; selecciona **Demo · datos simulados** para demostrar Naive Bayes y baseline.
6. Escribe una pregunta libre. Con Groq configurado, el modelo redacta la respuesta y usa herramientas; sin clave, se usa la respuesta local.


Las instrucciones exactas y los nombres de archivos están en [`evidencias/INSTRUCCIONES_CAPTURAS.md`](evidencias/INSTRUCCIONES_CAPTURAS.md). Guarda ahí las imágenes PNG/JPG que tomes con **Win + Shift + S**. No incluyas la clave ni la ventana del archivo `.env` en una captura.

## 4. Ejecutar las pruebas automatizadas

Desde la raíz del proyecto, con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Están en `tests/test_demo.py`. Verifican que el panel arranque sin API, que la predicción muestre comparación con baseline y que la búsqueda local invoque `search_docs`. No requieren pytest, conexión ni Groq. Son pruebas funcionales básicas; no reemplazan las 15 preguntas manuales de `docs/EVALUACION_AGENTE.md`.

## 5. Activar Groq (opcional)

La clave que se pegó en este chat debe considerarse expuesta: **revócala y genera una nueva antes de conectarla**. No pegues la clave en código, README, chat de evaluación, capturas ni `.env.example`.

1. Copia la plantilla local:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

2. En Notepad agrega la clave nueva después de `GROQ_API_KEY=` y guarda. El archivo `.env` está excluido por `.gitignore`.
3. Cierra e inicia de nuevo la app con `python -m streamlit run app.py`.

La integración habla con `api.groq.com` y envía el texto de la pregunta y el historial reciente para generar respuestas. El sistema ofrece tres herramientas: `get_pm25`, `predict_tomorrow` y `search_docs`; limita el loop a cuatro pasos por pregunta para evitar ciclos de llamadas. El modelo por defecto es `openai/gpt-oss-120b`; el listado y los avisos de retiro de modelos pueden cambiar, así que verifica la [documentación de modelos Groq](https://console.groq.com/docs/models) antes de actualizar `GROQ_MODEL`. Si la API no responde, la interfaz vuelve al modo local.

## 6. Fuente SIATA y CSV histórico

La app consulta automáticamente las capas públicas ICA PM2.5 del [geoportal SIATA](https://siata.gov.co/siata_nuevo/) (POECA y NO-POECA), con caché de cinco minutos. Incluye estación, concentración, categoría y actualización. La concentración es promedio móvil de 24 h, no dato instantáneo ([descripción del servicio GeoSAT](https://geosat.com.co/es/mapas/medellin/ambiente)). Si SIATA falla, hay advertencia y se usa la demo simulada.

Para un pronóstico entrenado/evaluado con historia verificable, carga un CSV histórico:

El IDEAM enlaza el conjunto **Calidad del Aire en Colombia** en [datos.gov.co](https://www.datos.gov.co/d/g4t8-zkc3) desde su [página de datos abiertos](https://www.ideam.gov.co/transparencia/datos-abiertos/seccion-de-datos-abiertos/calidad-del-aire-en-colombia). La app no descarga automáticamente esa serie histórica. Revisa el esquema y descarga un CSV desde la fuente oficial; confirma contaminante, unidad, estaciones, rango temporal y datos faltantes.

1. Conserva una copia sin modificar del CSV original y apunta URL, fecha de consulta y filtros.
2. Prepara una tabla CSV con columnas obligatorias `fecha,estacion,municipio,pm25`; `latitud,longitud` son opcionales. `fecha` debe poder leerse como fecha y `pm25` como número.
3. En la app, barra lateral → **Datos reales en CSV** → carga el archivo normalizado.
4. Confirma visualmente filas, estación y fechas. La app mostrará advertencia/éxito de carga; comprueba la unidad antes de interpretar resultados.
5. Repite la evaluación de Naive Bayes y baseline; reemplaza los resultados de demostración del informe por los obtenidos con datos reales y explica limitaciones.
6. Cita la fuente y el periodo en `docs/INFORME_FINAL.md` y en las capturas correspondientes.

Los documentos de contexto locales enlazan el portal IDEAM y un ejemplo de informe diario de [SIATA](https://siata.gov.co/). Las categorías didácticas calculadas para los CSV **no** son alertas oficiales ni consejo médico; en SIATA se muestra la categoría que publica la capa.

## 7. Qué documentos entregar y dónde completar

- `docs/INFORME_FINAL.md`: informe breve basado en la plantilla; completar equipo, fuente real, transformaciones, resultados y limitaciones. La guía del curso limita el informe a cuatro páginas.
- `docs/DECLARACION_USO_IA.md`: declarar Codex, Groq si se activa, propósito y revisión del equipo; completar nombres y fecha.
- `docs/EVALUACION_AGENTE.md`: ejecutar las 15 preguntas, registrar herramienta esperada/observada, resultado y captura. No dejar los campos `[pendiente]` en la entrega final.
- `evidencias/`: guardar capturas del dashboard, lecturas, predicción, búsqueda RAG y comparación del modelo siguiendo su instrucción.
- `tests/test_demo.py`: pruebas automatizadas reproducibles; el comando está en la sección 4.
- `knowledge/`: documentos locales del RAG y sus URLs originales.
- `data/demo_air_quality.csv`: datos simulados actuales para demo; `generar_datos_demo.py` los recrea con semilla fija.

## 8. Antes de subir la carpeta / repositorio

1. Revoca la clave expuesta y usa una nueva solo si decides activar Groq.
2. Revisa que `.env` no aparezca en el contenido que subirás; `.gitignore` ya lo excluye.
3. Sustituye la demostración por CSV real documentado o declara con claridad que el alcance entregado aún no cumple ese requisito.
4. Ejecuta pruebas, demo y las 15 preguntas manuales; guarda capturas en `evidencias/`.
5. Completa el informe y la declaración; elimina `[completar]` y `[pendiente]`.
6. Sigue en el PDF del curso la fecha, formato de correo y requisito de enviar el repositorio desde cada integrante.

## Limitaciones conocidas

SIATA depende de un servicio público y caché de cinco minutos; ofrece promedios de 24 h, no historial suficiente para pronosticar. El CSV incluido es simulado; las métricas Naive Bayes solo aplican al conjunto activo. El corpus RAG es pequeño y el modo offline no es un LLM. No usar esta app para decisiones de salud pública ni presentar datos simulados como reales.


