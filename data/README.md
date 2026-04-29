# Datos del proyecto

## OnlineRetail.csv

No se versiona en este repositorio. Es un dataset público que se
descarga aparte y se sube manualmente al volume de Databricks.

### Características

- Origen: UCI Machine Learning Repository, dataset "Online Retail"
- Tamaño: ~22 MB, ~541,909 filas
- Encoding: ISO-8859-1 (Latin-1) — crítico para lectura correcta
- Columnas: `InvoiceNo`, `StockCode`, `Description`, `Quantity`,
  `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`

### Fuentes

- UCI ML Repository: https://archive.ics.uci.edu/dataset/352/online+retail
- Repositorio del curso: https://github.com/si7006eafit/si7006-261

### Subida a Databricks

1. Catalog Explorer → `workspace` → `si7006_t2` → volume `raw_data`
2. Botón "Upload to this volume"
3. Seleccionar `OnlineRetail.csv` y confirmar
4. Path final: `/Volumes/workspace/si7006_t2/raw_data/OnlineRetail.csv`

El notebook `00_setup_validacion` confirma que el archivo se lee
correctamente y reporta el conteo de ~541,909 filas.