# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Ingesta Bronze con Auto Loader
# MAGIC
# MAGIC **Trabajo 2 SI7006 — Pipeline streaming end-to-end en Databricks**
# MAGIC
# MAGIC Este notebook lee los archivos JSON que el productor escribe en el
# MAGIC volume `stream_input/` y los ingesta a una tabla Delta Bronze
# MAGIC usando Auto Loader (Spark Structured Streaming).
# MAGIC
# MAGIC ## Decisiones de diseño
# MAGIC
# MAGIC - **Auto Loader (`cloudFiles`)** sobre `readStream.format("json")`
# MAGIC   clásico: optimizado para detectar archivos nuevos sin reescanear
# MAGIC   todo el directorio en cada trigger.
# MAGIC - **Schema explícito** en lugar de inferencia: documenta el contrato
# MAGIC   de la fuente y mejora performance.
# MAGIC - **Trigger.AvailableNow** en lugar de `processingTime`: el
# MAGIC   serverless de Databricks Free Edition no soporta triggers de
# MAGIC   streaming infinitos. `availableNow` procesa todos los archivos
# MAGIC   nuevos disponibles y termina; el patrón "siempre activo" se
# MAGIC   simula con un loop Python externo. Es el patrón **micro-batch
# MAGIC   incremental**, ampliamente usado en producción cuando la latencia
# MAGIC   aceptable es del orden de minutos.
# MAGIC - **Metadata de auditoría añadida en Bronze**: `ingested_at`,
# MAGIC   `source_file`, `source_file_size`, `source_file_modtime`. Bronze
# MAGIC   no transforma datos de negocio, pero sí añade trazabilidad.
# MAGIC - **`mergeSchema=true`**: permite que el schema evolucione si en el
# MAGIC   futuro se añaden columnas a la fuente.
# MAGIC
# MAGIC ## Cómo ejecutar
# MAGIC
# MAGIC 1. Asegurarse de que `00_setup_validacion` se ejecutó exitosamente.
# MAGIC 2. Ejecutar celdas 1 a 4 (configuración del stream).
# MAGIC 3. Ejecutar celda 5 (loop de ingesta) — bloquea el notebook
# MAGIC    durante toda la simulación.
# MAGIC 4. **En paralelo**, en otra ventana, correr el productor
# MAGIC    (`productor_eventos`) para generar los archivos JSON.
# MAGIC 5. Ejecutar celdas 6 a 8 para validar e inspeccionar la tabla.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 1 — Imports y configuración

# COMMAND ----------

import time

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType
)

# --- Configuración del proyecto (mismo que el notebook 00) ---
CATALOG = "workspace"
SCHEMA  = "si7006_t2"

VOL_STREAM_IN   = f"/Volumes/{CATALOG}/{SCHEMA}/stream_input"
VOL_CHECKPOINTS = f"/Volumes/{CATALOG}/{SCHEMA}/checkpoints"

TBL_BRONZE = f"{CATALOG}.{SCHEMA}.orders_bronze"

# Cada query streaming necesita SU PROPIO checkpoint en una carpeta única.
# El checkpoint guarda: qué archivos ya se procesaron, en qué offset, y
# el estado de cualquier agregación. Es lo que permite "exactly-once".
CHECKPOINT_BRONZE = f"{VOL_CHECKPOINTS}/bronze_orders"
SCHEMA_BRONZE     = f"{VOL_CHECKPOINTS}/bronze_orders_schema"

print(f"Stream input:        {VOL_STREAM_IN}")
print(f"Tabla Bronze:        {TBL_BRONZE}")
print(f"Checkpoint Bronze:   {CHECKPOINT_BRONZE}")
print(f"Schema location:     {SCHEMA_BRONZE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 2 — Definir schema explícito de los eventos
# MAGIC
# MAGIC Aunque Auto Loader puede inferir el schema, en proyectos serios
# MAGIC siempre se define explícitamente. Razones:
# MAGIC
# MAGIC 1. Evita sorpresas si llega un evento con tipos raros.
# MAGIC 2. Documenta el "contrato" de la fuente.
# MAGIC 3. Mejora performance (no hay que escanear archivos para inferir).

# COMMAND ----------

schema_eventos = StructType([
    StructField("InvoiceNo",   StringType(),    True),
    StructField("StockCode",   StringType(),    True),
    StructField("Description", StringType(),    True),
    StructField("Quantity",    IntegerType(),   True),
    StructField("InvoiceDate", TimestampType(), True),
    StructField("UnitPrice",   DoubleType(),    True),
    StructField("CustomerID",  IntegerType(),   True),
    StructField("Country",     StringType(),    True),
])

print("Schema definido:")
for campo in schema_eventos.fields:
    print(f"  {campo.name:15s} {campo.dataType.simpleString():15s} nullable={campo.nullable}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 3 — Crear el stream de lectura con Auto Loader

# COMMAND ----------

# Auto Loader es el conector recomendado para ingestar archivos que
# llegan a un directorio. Se configura con format("cloudFiles") y
# opciones específicas con prefijo "cloudFiles.".

df_stream_raw = (
    spark.readStream
        .format("cloudFiles")                                  # ← Auto Loader
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", SCHEMA_BRONZE)    # dónde guarda el schema
        .option("cloudFiles.inferColumnTypes", "false")        # usamos schema explícito
        .schema(schema_eventos)
        .option("cloudFiles.includeExistingFiles", "true")     # procesa archivos ya existentes al arrancar
        .load(VOL_STREAM_IN)
)

print("✓ Stream readStream configurado.")
print(f"  isStreaming: {df_stream_raw.isStreaming}")
print(f"\nSchema del DataFrame stream:")
df_stream_raw.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 4 — Enriquecer con metadata de auditoría
# MAGIC
# MAGIC La capa Bronze NO transforma datos de negocio (eso es Silver),
# MAGIC pero SÍ añade columnas técnicas de trazabilidad.

# COMMAND ----------

df_bronze = (
    df_stream_raw
        # Timestamp del momento exacto en que Spark procesó el registro
        .withColumn("ingested_at", F.current_timestamp())
        # Nombre del archivo de origen (Auto Loader expone _metadata.file_path)
        .withColumn("source_file", F.col("_metadata.file_path"))
        # Tamaño del archivo de origen
        .withColumn("source_file_size", F.col("_metadata.file_size"))
        # Timestamp de modificación del archivo
        .withColumn("source_file_modtime", F.col("_metadata.file_modification_time"))
)

print("Schema final de Bronze (datos + metadata):")
df_bronze.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 5 — Loop de ingesta incremental con Trigger.AvailableNow
# MAGIC
# MAGIC **Por qué un loop:** el serverless de Databricks Free Edition no
# MAGIC permite triggers infinitos (`processingTime`, `continuous`). Solo
# MAGIC permite `availableNow` (procesa lo nuevo y termina) y `once`.
# MAGIC
# MAGIC Para simular un stream "siempre activo", envolvemos el writeStream
# MAGIC en un loop Python que ejecuta una pasada cada N segundos. Cada
# MAGIC pasada es transaccional, idempotente, y respeta exactly-once
# MAGIC gracias al checkpoint.
# MAGIC
# MAGIC **IMPORTANTE:** esta celda bloquea el notebook durante toda la
# MAGIC corrida. Si el productor genera 30 lotes × 5s = 2.5 min, conviene
# MAGIC que el loop cubra ~3 min.

# COMMAND ----------

# Parámetros del loop — ajustar según duración del productor
ITERACIONES    = 20         # 20 * 12s = 4 min (margen sobre productor de 2.5 min)
PAUSA_SEGUNDOS = 12

filas_iniciales = spark.sql(f"SELECT COUNT(*) AS n FROM {TBL_BRONZE}").collect()[0]["n"] \
    if spark.catalog.tableExists(TBL_BRONZE) else 0

print(f"Filas iniciales en {TBL_BRONZE}: {filas_iniciales:,}")
print("=" * 80)

filas_acumuladas = 0

for i in range(1, ITERACIONES + 1):
    inicio = time.time()

    query = (
        df_bronze.writeStream
            .format("delta")
            .outputMode("append")
            .option("checkpointLocation", CHECKPOINT_BRONZE)
            .option("mergeSchema", "true")
            .trigger(availableNow=True)
            .toTable(TBL_BRONZE)
    )
    query.awaitTermination()

    # Reporte robusto: si lastProgress es None, no había trabajo nuevo;
    # si tiene datos, usar numInputRows.
    progreso = query.lastProgress
    if progreso is None:
        filas_nuevas = 0
        estado = "sin archivos nuevos"
    else:
        filas_nuevas = progreso.get("numInputRows") or 0
        estado = f"batchId={progreso.get('batchId')}"

    filas_acumuladas += filas_nuevas

    # Conteo real de la tabla (fuente de verdad)
    conteo_actual = spark.sql(f"SELECT COUNT(*) AS n FROM {TBL_BRONZE}").collect()[0]["n"]

    duracion = time.time() - inicio
    print(f"[{i:02d}/{ITERACIONES}] {time.strftime('%H:%M:%S')} "
          f"| {estado:25s} | nuevas: {filas_nuevas:4d} | "
          f"total tabla: {conteo_actual:6,} | {duracion:.1f}s")

    if i < ITERACIONES:
        time.sleep(PAUSA_SEGUNDOS)

filas_finales = spark.sql(f"SELECT COUNT(*) AS n FROM {TBL_BRONZE}").collect()[0]["n"]
print("=" * 80)
print(f"✓ Loop terminado.")
print(f"  Filas iniciales: {filas_iniciales:,}")
print(f"  Filas finales:   {filas_finales:,}")
print(f"  Filas añadidas:  {filas_finales - filas_iniciales:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 6 — Historial de operaciones Delta
# MAGIC
# MAGIC Cada commit streaming aparece como una operación independiente.
# MAGIC Esto es evidencia de las garantías ACID de Delta Lake.

# COMMAND ----------

print("Historial de operaciones sobre la tabla Bronze:")
spark.sql(f"DESCRIBE HISTORY {TBL_BRONZE}").select(
    "version", "timestamp", "operation",
    "operationMetrics.numOutputRows",
    "operationMetrics.numOutputBytes"
).show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 7 — Validación final de Bronze

# COMMAND ----------

# Resumen agregado
print("RESUMEN BRONZE:")
spark.sql(f"""
    SELECT
        COUNT(*) AS total_filas,
        COUNT(DISTINCT source_file) AS archivos_distintos,
        COUNT(DISTINCT InvoiceNo) AS invoices_distintos,
        MIN(ingested_at) AS primer_ingest,
        MAX(ingested_at) AS ultimo_ingest
    FROM {TBL_BRONZE}
""").show(truncate=False)

# Muestra de filas
print("MUESTRA DE 5 FILAS RECIENTES:")
spark.sql(f"""
    SELECT InvoiceNo, StockCode, Description, Quantity, UnitPrice,
           Country, ingested_at, source_file
    FROM {TBL_BRONZE}
    ORDER BY ingested_at DESC
    LIMIT 5
""").show(truncate=False)

# Distribución por archivo origen
print("DISTRIBUCIÓN POR LOTE (TOP 10 RECIENTES):")
spark.sql(f"""
    SELECT
        regexp_extract(source_file, 'orders_[0-9_]+_lote([0-9]+)\\\\.json', 1) AS lote,
        COUNT(*) AS eventos,
        MIN(ingested_at) AS primer_ingest,
        MAX(ingested_at) AS ultimo_ingest
    FROM {TBL_BRONZE}
    WHERE source_file LIKE '%orders_%lote%.json'
    GROUP BY lote
    ORDER BY lote DESC
    LIMIT 10
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 8 — (Opcional) Reset completo de Bronze
# MAGIC
# MAGIC **NO ejecutar en flujo normal.** Solo si se necesita empezar de cero
# MAGIC (por ejemplo, antes de grabar el video de sustentación con datos
# MAGIC limpios y un conteo exacto).
# MAGIC
# MAGIC Borra: tabla Delta + checkpoint + schema location.
# MAGIC Tras el reset, las celdas 1-4 se re-ejecutan y la celda 5 procesa
# MAGIC todos los archivos en `stream_input/` como si fueran nuevos.

# COMMAND ----------

EJECUTAR_RESET = False   # cambiar a True solo cuando se necesite reset

if EJECUTAR_RESET:
    print("⚠ RESET de Bronze. Borrando:")

    try:
        spark.sql(f"DROP TABLE IF EXISTS {TBL_BRONZE}")
        print(f"  ✓ Tabla {TBL_BRONZE} eliminada")
    except Exception as e:
        print(f"  ⚠ {e}")

    try:
        dbutils.fs.rm(CHECKPOINT_BRONZE, recurse=True)
        print(f"  ✓ Checkpoint {CHECKPOINT_BRONZE} eliminado")
    except Exception as e:
        print(f"  ⚠ {e}")

    try:
        dbutils.fs.rm(SCHEMA_BRONZE, recurse=True)
        print(f"  ✓ Schema location {SCHEMA_BRONZE} eliminado")
    except Exception as e:
        print(f"  ⚠ {e}")

    print("\n✓ Reset completado. Re-ejecutar celdas 1-5 para reprocesar.")
else:
    print("Reset desactivado. Cambiar EJECUTAR_RESET=True si se necesita.")
