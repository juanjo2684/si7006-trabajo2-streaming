# Databricks notebook source
# MAGIC %md
# MAGIC # Productor de eventos vivos
# MAGIC
# MAGIC **Trabajo 2 SI7006 — Pipeline streaming end-to-end en Databricks**
# MAGIC
# MAGIC Este notebook simula un sistema de e-commerce que va generando
# MAGIC órdenes en tiempo real, escribiendo lotes de eventos como archivos
# MAGIC JSON Lines (NDJSON) en un volumen de Unity Catalog.
# MAGIC
# MAGIC Estos archivos son consumidos por el notebook `01_bronze_ingesta`
# MAGIC mediante Auto Loader (Spark Structured Streaming).
# MAGIC
# MAGIC ## Decisiones de diseño
# MAGIC
# MAGIC - **Lotes de N eventos por archivo** (no eventos individuales) para
# MAGIC   evitar el "small files problem" en Delta Lake. Es el patrón usado
# MAGIC   en producción por sistemas como Kinesis Firehose.
# MAGIC - **Sobrescritura de `InvoiceDate` con timestamp actual**: las fechas
# MAGIC   originales del dataset son de 2010-2011. Sobrescribir con `now()`
# MAGIC   permite que las ventanas tumbling/sliding en Silver y Gold trabajen
# MAGIC   sobre tiempos coherentes con el momento de la demo.
# MAGIC - **Mezcla aleatoria del dataset** con `random_state=42` para que cada
# MAGIC   lote contenga órdenes "variadas" en lugar de ordenadas por fecha.
# MAGIC
# MAGIC ## Cómo ejecutar
# MAGIC
# MAGIC 1. Asegurarse de que `00_setup_validacion` se ejecutó exitosamente.
# MAGIC 2. Ejecutar celdas 1 a 4 (preparación).
# MAGIC 3. (Opcional) Ejecutar celda 5 para limpiar archivos previos en `stream_input`.
# MAGIC 4. Ejecutar celda 6 (loop de producción) — bloquea el notebook
# MAGIC    durante toda la simulación.
# MAGIC 5. **En paralelo**, en otra ventana del navegador, ejecutar el loop
# MAGIC    del notebook `01_bronze_ingesta` para ver los datos siendo ingeridos.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 1 — Imports y configuración

# COMMAND ----------

# Imports y configuración del productor

import json
import time
from datetime import datetime
import pandas as pd

# --- Configuración del proyecto (mismo que el notebook 00) ---
CATALOG = "workspace"
SCHEMA  = "si7006_t2"

VOL_RAW       = f"/Volumes/{CATALOG}/{SCHEMA}/raw_data"
VOL_STREAM_IN = f"/Volumes/{CATALOG}/{SCHEMA}/stream_input"

CSV_ORIGEN = f"{VOL_RAW}/OnlineRetail.csv"

# --- Parámetros del productor ---
EVENTOS_POR_LOTE     = 50    # cuántas órdenes por archivo JSON
SEGUNDOS_ENTRE_LOTES = 5     # cada cuánto se escribe un nuevo archivo
LOTES_TOTALES        = 30    # total de lotes a generar (30 * 5s = 2.5 min)
                              # Ajustar para demos más cortas/largas.
                              # Recomendado: 30-60 lotes para demo del video.

print(f"Origen:           {CSV_ORIGEN}")
print(f"Destino streams:  {VOL_STREAM_IN}")
print(f"Eventos/lote:     {EVENTOS_POR_LOTE}")
print(f"Segundos/lote:    {SEGUNDOS_ENTRE_LOTES}")
print(f"Lotes totales:    {LOTES_TOTALES}")
print(f"Duración total:   ~{LOTES_TOTALES * SEGUNDOS_ENTRE_LOTES / 60:.1f} minutos")
print(f"Eventos totales:  {LOTES_TOTALES * EVENTOS_POR_LOTE:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 2 — Cargar el CSV una sola vez a memoria

# COMMAND ----------

# Cargar el dataset completo a un DataFrame de Pandas
# IMPORTANTE: encoding ISO-8859-1 porque OnlineRetail tiene caracteres
# Latin-1 en las descripciones de productos (ej. "Café", "Crème")

df_pandas = pd.read_csv(
    CSV_ORIGEN,
    encoding="ISO-8859-1",
    dtype={
        "InvoiceNo":   str,
        "StockCode":   str,
        "Description": str,
        "Quantity":    "Int64",     # Int64 nullable de pandas
        "UnitPrice":   float,
        "CustomerID":  "Int64",
        "Country":     str
    },
    parse_dates=["InvoiceDate"]
)

print(f"Filas cargadas: {len(df_pandas):,}")
print(f"Columnas:       {list(df_pandas.columns)}")
print(f"\nPrimeras filas:")
print(df_pandas.head(3))

# Mezclar aleatoriamente para que cada lote se vea como órdenes "nuevas"
# y no llegue ordenado por fecha (más realista como flujo de e-commerce)
df_pandas = df_pandas.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n✓ Dataset listo en memoria, mezclado aleatoriamente.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 3 — Función auxiliar para serializar lote a JSON Lines

# COMMAND ----------

# Función que toma un slice del DataFrame y lo escribe como
# archivo JSON Lines (NDJSON) en el volumen de stream_input.
#
# JSON Lines es el formato preferido para streaming: una línea = un evento.
# Auto Loader lo lee de forma natural con format("json").

def escribir_lote_json(df_lote: pd.DataFrame, ruta_destino: str, nombre_archivo: str):
    """
    Serializa un lote de órdenes como NDJSON y lo escribe al volumen.

    Args:
        df_lote: subconjunto del DataFrame con las órdenes a escribir.
        ruta_destino: ruta del Volume (ej. /Volumes/.../stream_input).
        nombre_archivo: nombre del archivo .json a crear.

    Returns:
        Ruta completa del archivo escrito.
    """
    # orient="records" + lines=True genera NDJSON (una línea por fila)
    # date_format="iso" → InvoiceDate sale como string ISO 8601
    lineas = df_lote.to_json(
        orient="records",
        lines=True,
        date_format="iso"
    )

    # Los Volumes de Unity Catalog se acceden con paths normales del
    # filesystem desde un cluster Databricks
    ruta_completa = f"{ruta_destino}/{nombre_archivo}"
    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(lineas)

    return ruta_completa


# Test rápido: escribir un lote de prueba
df_test = df_pandas.head(5)
ruta_test = escribir_lote_json(
    df_test,
    VOL_STREAM_IN,
    f"test_inicial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)
print(f"✓ Archivo de prueba escrito: {ruta_test}")

# Verificar contenido
with open(ruta_test, "r", encoding="utf-8") as f:
    contenido = f.read()
print(f"\nContenido (primeras 500 chars):")
print(contenido[:500])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 4 — (Opcional) Limpiar archivos previos
# MAGIC
# MAGIC Para una corrida limpia (especialmente antes de grabar el video),
# MAGIC ejecutar esta celda. En entornos productivos NUNCA se limpia así
# MAGIC una zona de ingesta — esto es solo para demo.

# COMMAND ----------

archivos_existentes = dbutils.fs.ls(VOL_STREAM_IN)
print(f"Archivos antes de limpiar: {len(archivos_existentes)}")

for archivo in archivos_existentes:
    dbutils.fs.rm(archivo.path)

print(f"✓ Directorio {VOL_STREAM_IN} limpio.")
print(f"Archivos después: {len(dbutils.fs.ls(VOL_STREAM_IN))}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 5 — Loop principal del productor
# MAGIC
# MAGIC **IMPORTANTE:** esta celda BLOQUEA el notebook mientras corre.
# MAGIC Para detenerla manualmente: botón "Cancel" en la celda.
# MAGIC
# MAGIC Mientras corre, OTRO notebook (`01_bronze_ingesta`) debe estar
# MAGIC ejecutando el loop con `Trigger.AvailableNow` para procesar los
# MAGIC archivos a medida que se generan.

# COMMAND ----------

print("=" * 60)
print(f"INICIANDO PRODUCCIÓN DE EVENTOS")
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

filas_totales = len(df_pandas)
posicion = 0

for lote_num in range(1, LOTES_TOTALES + 1):
    # Tomar el siguiente slice. Si llegamos al final, recomenzar desde 0
    inicio = posicion % filas_totales
    fin = inicio + EVENTOS_POR_LOTE
    df_lote = df_pandas.iloc[inicio:fin].copy()

    # Sobrescribir InvoiceDate con timestamp actual para simular órdenes
    # llegando en vivo. CLAVE para que las ventanas de tiempo en Silver
    # y Gold reflejen el momento real de la simulación.
    df_lote["InvoiceDate"] = datetime.now()

    # Nombre del archivo con timestamp y número de lote
    nombre = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}_lote{lote_num:04d}.json"
    ruta = escribir_lote_json(df_lote, VOL_STREAM_IN, nombre)

    print(f"  [{lote_num:03d}/{LOTES_TOTALES}] {datetime.now().strftime('%H:%M:%S')} "
          f"→ {len(df_lote)} eventos → {nombre}")

    posicion += EVENTOS_POR_LOTE

    # No dormir después del último lote
    if lote_num < LOTES_TOTALES:
        time.sleep(SEGUNDOS_ENTRE_LOTES)

print("=" * 60)
print(f"PRODUCCIÓN TERMINADA")
print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Archivos generados: {LOTES_TOTALES}")
print(f"Eventos totales:    {LOTES_TOTALES * EVENTOS_POR_LOTE:,}")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Celda 6 — Validación post-producción

# COMMAND ----------

archivos = dbutils.fs.ls(VOL_STREAM_IN)
print(f"Total de archivos en stream_input: {len(archivos)}")
print(f"Tamaño total: {sum(a.size for a in archivos) / 1024:.1f} KB")
print(f"\nÚltimos 5 archivos generados:")
for a in sorted(archivos, key=lambda x: x.modificationTime)[-5:]:
    print(f"  {a.name}  ({a.size:,} bytes)")
