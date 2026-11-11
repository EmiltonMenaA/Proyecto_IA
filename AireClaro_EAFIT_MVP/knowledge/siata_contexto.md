# SIATA: datos recientes de PM2.5 del Valle de Aburrá
El geoportal oficial de SIATA ofrece las capas «ICA - PM2.5 Estaciones POECA» y «ICA - PM2.5 Estaciones NO POECA». El MVP consulta el servicio público de carga de capas `https://siata.gov.co/siata_nuevo/index.php/capa_service/consultar_capa_carga` con los identificadores de esas capas y extrae concentración, categoría oficial, código de estación, municipio y hora de actualización.

La capa consultada representa el promedio móvil de las últimas 24 horas por estación; no es una lectura instantánea ni un pronóstico. La caché del MVP dura cinco minutos. Se muestran los códigos de estación tal como vienen del servicio para no inventar nombres. Si el servicio falla, la app lo indica y cambia a datos simulados solo como respaldo.

Portal/geoportal oficial de SIATA: https://siata.gov.co/siata_nuevo/
Metodología de PM2.5 del Valle de Aburrá: https://www.metropol.gov.co/ambiental/calidad-del-aire/
Ejemplo de informe diario: https://siata.gov.co/CalidadAire/InformesDiarios/Informe_AMVA_22032025.pdf
