# Datos del proyecto

## OnlineRetail.csv

**No se versiona en este repositorio** porque pesa ~22 MB y los datos no
son del equipo (son públicos). Este archivo se descarga aparte y se sube
manualmente al volume de Databricks.

### Características

- **Origen:** UCI Machine Learning Repository, dataset "Online Retail"
- **Tamaño:** ~22 MB, ~541,909 filas
- **Encoding:** ISO-8859-1 (Latin-1) — *crítico para leerlo correctamente*
- **Columnas:**
  - `InvoiceNo` (string) — número de factura
  - `StockCode` (string) — código de producto
  - `Description` (string) — descripción del producto
  - `Quantity` (int) — cantidad ordenada (negativo si es devolución)
  - `InvoiceDate` (timestamp) — fecha y hora de la transacción
  - `UnitPrice` (double) — precio unitario en GBP
  - `CustomerID` (int, nullable) — ID del cliente
  - `Country` (string) — país del cliente

### Cómo obtenerlo

Disponible en múltiples fuentes públicas:

- UCI ML Repository: https://archive.ics.uci.edu/dataset/352/online+retail
- Kaggle: https://www.kaggle.com/datasets/carrie1/ecommerce-data
- También está disponible en el repositorio del curso SI7006:
  https://github.com/si7006eafit/si7006-261

### Cómo subirlo a Databricks

1. Catalog Explorer → catálogo `workspace` → schema `si7006_t2`
2. Volume `raw_data` → botón "Upload to this volume"
3. Seleccionar `OnlineRetail.csv` desde local
4. Confirmar subida
5. Path final: `/Volumes/workspace/si7006_t2/raw_data/OnlineRetail.csv`

### Validación post-subida

Ejecutar el notebook `00_setup_validacion`. La celda 3 valida que:
- El archivo existe en el volume.
- El conteo total de filas es ~541,909.
- El schema se lee correctamente con encoding Latin-1.
