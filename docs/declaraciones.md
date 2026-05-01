# Declaraciones de honestidad académica

## 1. Fuentes externas reutilizadas

### Material del curso SI7006

- `databricks_pyspark_lakehouse_demo.ipynb` — patrón Medallion y uso
  de Volumes de Unity Catalog.
- `Lab_Delta_Lake.ipynb` — patrones de creación de tablas Delta.
- Repositorio oficial del curso:
  https://github.com/si7006eafit/si7006-261

### Documentación oficial

- Databricks Auto Loader:
- Spark Structured Streaming Programming Guide
- Delta Lake

### Dataset

- OnlineRetail.csv — UCI ML Repository:
  https://archive.ics.uci.edu/dataset/352/online+retail

## 2. Aporte individual

### Juan José Morales (Ingesta)

- Setup de Unity Catalog (catálogo, schema, volumes).
- Notebook `00_setup_validacion`.
- Productor de eventos (`productor_eventos.py`).
- Notebook `01_bronze_ingesta` con Auto Loader.

### Sebastian Ruiz (Capa Silver)

- Notebook `02_silver_limpieza` con dedup stateful y watermark.
- Resolución del problema de trigger en Free Edition.

### Santiago Molano

- Notebook `03_gold_kpis`
- Notebook `03_gold_alertas_reorden`

### Daniel Pareja

- Consultas SQL
- Diseño y generacion de dashboard

## 4. Declaración firmada

Los integrantes del equipo declaramos que:

1. Las contribuciones documentadas son verídicas.
2. El uso de IA generativa se limitó a planeación, generación inicial
   de código y depuración, con validación en el entorno real.
3. Las fuentes externas usadas están explícitamente declaradas.
4. El código fue ejecutado en Databricks Free Edition por al menos
   uno de los integrantes.

Fecha: 30 de abril de 2026