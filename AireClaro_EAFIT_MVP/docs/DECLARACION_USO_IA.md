# Declaración de uso de inteligencia artificial generativa

**Proyecto:** AireClaro · **Curso:** SI3003 · **Equipo:** Individual · **Integrante:** Emilton Mena Acevedo · **Fecha:** 11 de noviembre de 2026

Durante la preparación de este MVP se utilizó **OpenAI Codex** como asistente de programación para proponer y editar estructura de archivos, interfaz Streamlit, documentación, pruebas automatizadas y preguntas de evaluación. El equipo debe revisar, ejecutar y comprender el código antes de entregarlo; la herramienta no sustituye la verificación de los resultados.

La aplicación permite conectar opcionalmente el chat con **Groq** (modelo configurado en `.env.example`) para redactar respuestas y decidir cuándo llamar a las herramientas. El modo de demostración sin clave genera respuestas locales deterministas y no usa un LLM. El agente busca en documentos guardados dentro del proyecto y consulta la capa pública de SIATA para PM2.5 reciente cuando esa fuente está seleccionada; también puede leer un CSV cargado. SIATA informa promedios móviles de 24 horas por estación, no datos instantáneos.

**Datos:** la fuente predeterminada para observaciones recientes es la capa pública ICA PM2.5 de SIATA, consultada en línea; el sistema conserva fecha/hora, estación, concentración y categoría de la capa. La app usa un CSV simulado solo como demostración de respaldo o cuando el usuario selecciona Demo. Si se agrega un CSV histórico del IDEAM/AMVA, registrar aquí URL, fecha de descarga, variables y transformaciones.

**Verificación del integrante:** [completar después de revisar personalmente el código, las pruebas, los resultados y el funcionamiento del modelo y de las herramientas].

**Declaración final:** confirmo que la descripción anterior refleja el uso de IA generativa en esta entrega. Completar esta declaración después de revisar la implementación y los resultados.

Nombre y firma: Emilton Mena Acevedo



