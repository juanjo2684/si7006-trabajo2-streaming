# SI7006 — Trabajo 2: Pipeline streaming end-to-end en Databricks

Maestría en Ciencia de Datos y Analítica — Universidad EAFIT — 2026-1
Curso: SI7006 Almacenamiento y Procesamiento de Grandes Datos
Fecha de entrega: 30 de abril de 2026

## Equipo

- Juan José Morales
- Sebastian Ruiz
- Santiago Molano
- Daniel pareja

## Caso de uso

Monitoreo en tiempo real de órdenes en retail/e-commerce usando el
dataset OnlineRetail.csv como fuente de eventos simulados.

## Arquitectura

```
OnlineRetail.csv
│
▼
Productor Python  ──►  /Volumes/.../stream_input/*.json
│
▼
Auto Loader (Trigger.AvailableNow)
│
▼
orders_bronze (Delta + metadata)
│
▼
orders_silver (Delta limpio)
│
▼
gold_kpi_ventana   gold_alertas_reorder (Delta)
│
▼
AI/BI Dashboard de Databricks
```

## Stack

- Databricks Free Edition (serverless)
- Apache Spark Structured Streaming (PySpark)
- Delta Lake sobre Volumes de Unity Catalog
- Auto Loader (`cloudFiles`) con `Trigger.AvailableNow`
- AI/BI Dashboards de Databricks

## Estructura del repositorio

## Estructura del repositorio

```
si7006-trabajo2-streaming/
├── README.md
├── .gitignore
├── notebooks/
│   ├── 00_setup_validacion.py
│   ├── 01_bronze_ingesta.py
│   ├── 02_silver_limpieza.py
│   ├── 03_gold_kpis.py
│   └── 04_gold_alertas_reorder.py
├── productor/
│   └── productor_eventos.py
├── data/
│   └── README.md
├── docs/
    ├── informe_tecnico.md
    └── declaraciones.md

```

## Cómo reproducir

### Prerrequisitos

1. Cuenta Databricks Free Edition con workspace activo.
2. `OnlineRetail.csv` descargado (ver `data/README.md`).

### Setup

1. En Catalog Explorer del workspace:
   - Crear schema `si7006_t2` en el catálogo `workspace`.
   - Crear 3 Volumes (Managed): `raw_data`, `stream_input`, `checkpoints`.
   - Subir `OnlineRetail.csv` al volume `raw_data`.
2. Importar los `.py` de `notebooks/` y `productor/` como notebooks.
3. Ejecutar `00_setup_validacion` y verificar que las 4 celdas pasen.

### Corrida del pipeline (en este orden)

1. `01_bronze_ingesta` → Run All. Dejar corriendo.
2. `productor_eventos` → Run All en otra pestaña inmediatamente después.
3. Esperar a que ambos terminen (~4 min).
4. `02_silver_limpieza` → Run All.
5. `03_gold_kpis` y `04_gold_alertas_reorder` → Run All.

## Etapas del proyecto

- Fase 0 — Setup y validación
- Fase 1 — Productor + Bronze
- Fase 2 — Silver
- Fase 3 — Gold (KPIs y alertas)
- Fase 4 — Dashboard AI/BI
- Fase 5 — Informe + video

## Decisiones técnicas clave

| Decisión | Justificación |
|---|---|
| Lotes de 50 eventos por archivo JSON | Evita el "small files problem" en Delta |
| Auto Loader (`cloudFiles`) | Manejo nativo de archivos incrementales y schema |
| Schema explícito | Documenta el contrato de la fuente |
| `Trigger.AvailableNow` + loop Python | Free Edition serverless no soporta triggers infinitos |
| `InvoiceDate` reescrito con `now()` en productor | Permite que las ventanas de Gold trabajen sobre tiempos coherentes |
| `dropDuplicatesWithinWatermark` 24h | Dedup stateful con estado acotado |
| Conservar filas guest (CustomerID null) | Evita subestimar el ingreso total en Gold |

## Declaraciones

Ver `docs/declaraciones.md`.
