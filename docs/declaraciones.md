# Declaraciones de honestidad académica

Este documento recopila las declaraciones explícitas exigidas por el
curso SI7006 sobre el uso de IA generativa, fuentes externas reutilizadas
y el aporte individual de cada integrante del equipo.

## 1. Uso de IA generativa

*[Cada integrante debe completar su sección. Plantilla:]*

### Juan José Morales Guzmán

- **Herramienta usada:** Claude (modelo Opus de Anthropic), accedido vía
  claude.ai con un proyecto que contiene el material del curso SI7006.
- **Uso:** asistencia en planeación de fases, diseño de la arquitectura
  del pipeline, generación inicial de código PySpark, depuración de
  errores específicos de Databricks Free Edition, redacción de
  secciones del informe.
- **Validación:** todo el código generado fue ejecutado, validado y
  ajustado en el entorno real. Los errores encontrados (como el de
  `INFINITE_STREAMING_TRIGGER_NOT_SUPPORTED`) llevaron a iteraciones
  conjuntas con la herramienta para llegar a soluciones funcionales.
- **No se usó IA para:** la subida manual de archivos al volume, la
  ejecución de notebooks, la captura de evidencias, las decisiones
  finales sobre qué incluir en el informe.

### [Nombre 2]

*[Completar.]*

### [Nombre 3]

*[Completar.]*

### [Nombre 4]

*[Completar.]*

---

## 2. Fuentes externas y código reutilizado

### Material del curso SI7006

Se reutilizó (con adaptaciones) código y patrones de los siguientes
recursos provistos por el curso:

- `Lab_Delta_Lake.ipynb` — patrón de creación de tablas Delta y manejo
  de schemas.
- `databricks_pyspark_lakehouse_demo.ipynb` — patrón Medallion
  (Bronze/Silver/Gold) y uso de Volumes de Unity Catalog.
- Repositorio del curso: https://github.com/si7006eafit/si7006-261
  (carpeta `streaming/spark-streaming` para referencias de Structured
  Streaming).

### Documentación oficial

- Databricks Auto Loader:
  https://docs.databricks.com/en/ingestion/auto-loader/index.html
- Spark Structured Streaming Programming Guide:
  https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- Delta Lake:
  https://docs.delta.io/latest/index.html

### Dataset

- OnlineRetail.csv — UCI Machine Learning Repository, dataset público:
  https://archive.ics.uci.edu/dataset/352/online+retail

---

## 3. Aporte individual de cada estudiante

### Juan José Morales Guzmán (Tech Lead / Ingesta)

- Coordinación general del proyecto y planeación de fases.
- Setup del workspace Databricks y creación de la estructura Unity
  Catalog (catálogo, schema, volumes).
- Implementación del notebook `00_setup_validacion`.
- Implementación del productor de eventos (`productor_eventos.py`).
- Implementación del notebook `01_bronze_ingesta` con Auto Loader.
- Resolución del problema de trigger en Free Edition.
- Documentación de las decisiones técnicas en el informe.
- *[Añadir aportes en fases siguientes.]*

### [Nombre 2] — Procesamiento / Streaming

*[Completar tras Fase 2 y 3.]*

### [Nombre 3] — Calidad y Eventos

*[Completar tras Fase 2, 3 y 5.]*

### [Nombre 4] — Visualización y Documentación

*[Completar tras Fase 4 y 6.]*

---

## 4. Declaración firmada

Los integrantes del equipo declaramos que:

1. Las contribuciones documentadas arriba son verídicas y reflejan el
   aporte real de cada uno.
2. El uso de IA generativa se limitó a asistencia en planeación,
   generación inicial de código y depuración, siempre con validación
   y ajuste posterior en el entorno real.
3. Las fuentes externas usadas están explícitamente declaradas.
4. El código entregado fue ejecutado y probado en Databricks Free
   Edition por al menos uno de los integrantes.

**Fecha de declaración:** 30 de abril de 2026
