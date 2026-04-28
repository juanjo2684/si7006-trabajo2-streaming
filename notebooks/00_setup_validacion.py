# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Setup y validación del entorno
# MAGIC
# MAGIC **Trabajo 2 SI7006 — Pipeline streaming end-to-end en Databricks**
# MAGIC
# MAGIC Este notebook valida que:
# MAGIC - Spark y Delta Lake están disponibles en la versión correcta.
# MAGIC - El catálogo, schema y volumes de Unity Catalog existen.
# MAGIC - El archivo `OnlineRetail.csv` está accesible en el volume `raw_data`.
# MAGIC - Tenemos permisos de escritura para crear tablas Delta.
# MAGIC
# MAGIC Cada integrante del equipo debe ejecutar este notebook **una vez**
# MAGIC en su propio workspace Databricks Free Edition antes de avanzar
# MAGIC al notebook de ingesta Bronze.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 1 — Validación de versiones del entorno

# COMMAND ----------

# Validación del entorno Databricks Free Edition
# Objetivo: confirmar que tenemos Spark, Delta Lake y Python con versiones compatibles

import sys
import pyspark
from delta import __version__ as delta_version

print("=" * 60)
print("VALIDACIÓN DEL ENTORNO")
print("=" * 60)
print(f"Python:     {sys.version.split()[0]}")
print(f"PySpark:    {pyspark.__version__}")
print(f"Delta Lake: {delta_version}")
print(f"Spark:      {spark.version}")
print(f"Usuario:    {spark.sql('SELECT current_user()').collect()[0][0]}")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 2 — Variables del proyecto
# MAGIC
# MAGIC Estas variables se reusan en todos los notebooks del pipeline.
# MAGIC Si tu catálogo se llama distinto a `workspace`, ajustarlo aquí.

# COMMAND ----------

# Configuración de catálogo, schema y paths de Volumes
# IMPORTANTE: ajustar CATALOG al que aparezca en TU Catalog Explorer.
# En Free Edition suele ser "workspace". Si es otro, cambiarlo aquí.

CATALOG = "workspace"
SCHEMA  = "si7006_t2"

# Paths a los Volumes (creados manualmente en el Catalog Explorer)
VOL_RAW         = f"/Volumes/{CATALOG}/{SCHEMA}/raw_data"
VOL_STREAM_IN   = f"/Volumes/{CATALOG}/{SCHEMA}/stream_input"
VOL_CHECKPOINTS = f"/Volumes/{CATALOG}/{SCHEMA}/checkpoints"

# Tablas Delta (notación de tres niveles: catalog.schema.table)
TBL_BRONZE      = f"{CATALOG}.{SCHEMA}.orders_bronze"
TBL_SILVER      = f"{CATALOG}.{SCHEMA}.orders_silver"
TBL_GOLD_KPI    = f"{CATALOG}.{SCHEMA}.gold_kpi_ventana"
TBL_GOLD_ALERTS = f"{CATALOG}.{SCHEMA}.gold_alertas_reorder"

print(f"Catálogo:        {CATALOG}")
print(f"Esquema:         {SCHEMA}")
print(f"Raw data:        {VOL_RAW}")
print(f"Stream input:    {VOL_STREAM_IN}")
print(f"Checkpoints:     {VOL_CHECKPOINTS}")
print(f"Tabla Bronze:    {TBL_BRONZE}")
print(f"Tabla Silver:    {TBL_SILVER}")
print(f"Tabla Gold KPI:  {TBL_GOLD_KPI}")
print(f"Tabla Gold Alts: {TBL_GOLD_ALERTS}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 3 — Verificar que el CSV está accesible
# MAGIC
# MAGIC Confirma que `OnlineRetail.csv` fue subido correctamente al volume
# MAGIC `raw_data` y que se puede leer con el encoding correcto (Latin-1).

# COMMAND ----------

# Confirmar que OnlineRetail.csv está en el volumen raw_data
# y mostrar las primeras filas para sanity check

csv_path = f"{VOL_RAW}/OnlineRetail.csv"

# Verificar que el archivo existe en el volumen
files_in_raw = dbutils.fs.ls(VOL_RAW)
print("Archivos en raw_data:")
for f in files_in_raw:
    print(f"  - {f.name}  ({f.size:,} bytes)")

# Leer una muestra pequeña para validar formato
# IMPORTANTE: el CSV original viene con encoding ISO-8859-1 (Latin-1),
# no UTF-8. Si no se especifica, las descripciones con tildes salen mal.
df_muestra = (
    spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .option("encoding", "ISO-8859-1")
        .csv(csv_path)
        .limit(10)
)

print("\nEsquema detectado:")
df_muestra.printSchema()

print("\nPrimeras 10 filas:")
df_muestra.show(truncate=False)

# Conteo total
total = (
    spark.read
        .option("header", "true")
        .option("encoding", "ISO-8859-1")
        .csv(csv_path)
        .count()
)
print(f"\nTotal de filas en el CSV completo: {total:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 4 — Crear schema y validar permisos de escritura

# COMMAND ----------

# Crear schema (idempotente) y validar que podemos escribir tablas Delta

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"SHOW SCHEMAS IN {CATALOG}").show(truncate=False)

# Test de escritura: crear una tabla Delta dummy y borrarla
test_table = f"{CATALOG}.{SCHEMA}.test_setup"
(
    spark.range(5)
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(test_table)
)
print(f"\n✓ Tabla de prueba creada: {test_table}")
spark.sql(f"SELECT * FROM {test_table}").show()

# Limpiar
spark.sql(f"DROP TABLE {test_table}")
print(f"✓ Tabla de prueba eliminada. Permisos de escritura: OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resumen
# MAGIC
# MAGIC Si todas las celdas anteriores se ejecutaron sin error, el entorno
# MAGIC está listo para los notebooks siguientes:
# MAGIC
# MAGIC 1. `productor_eventos.py` — genera archivos JSON simulando órdenes en vivo.
# MAGIC 2. `01_bronze_ingesta.py` — ingesta streaming de los JSON a tabla Delta Bronze.
# MAGIC 3. `02_silver_limpieza.py` — limpieza y enriquecimiento (siguiente fase).
# MAGIC 4. `03_gold_kpis.py` — agregaciones con ventanas (siguiente fase).
# MAGIC 5. `04_gold_alertas_reorder.py` — eventos de reorder y anomalías (siguiente fase).
