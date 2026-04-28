# Evidencias del proyecto

Capturas de pantalla y artefactos por cada fase del pipeline.

## Estructura

- `fase0/` — setup del entorno (catálogo, schema, volumes, CSV subido,
  notebook 00 ejecutado).
- `fase1/` — productor de eventos + ingesta Bronze.
- `fase2/` — capa Silver (pendiente).
- `fase3/` — capa Gold (pendiente).
- `fase4/` — dashboard AI/BI (pendiente).
- `fase5/` — Time Travel y robustez (pendiente).

## Capturas mínimas requeridas para Fase 1

1. **`productor_output.png`** — output del notebook productor mostrando
   los 30 lotes generados con timestamps.
2. **`bronze_loop_output.png`** — output del loop de ingesta mostrando
   filas siendo procesadas y conteo creciendo.
3. **`bronze_table_catalog.png`** — Catalog Explorer mostrando la tabla
   `orders_bronze` creada con sus 12 columnas (8 de negocio + 4 de
   metadata).
4. **`bronze_describe_history.png`** — output del comando
   `DESCRIBE HISTORY` mostrando los commits streaming registrados.
5. **`bronze_validacion_final.png`** — output de la celda 7 del notebook
   Bronze (resumen, muestra de filas, distribución por lote).
6. **`stream_input_files.png`** — directorio `stream_input/` mostrando
   los 30 archivos JSON generados por el productor.

## Cómo capturar

- Captura completa del notebook desde el botón derecho del navegador,
  o usar herramientas de captura del sistema operativo.
- Nombrar archivos con el patrón `<faseN>_<descripcion>.png` para
  facilitar la búsqueda.
- Resolución mínima: legible al 100% sin zoom.
