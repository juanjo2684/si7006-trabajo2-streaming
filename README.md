# SI7006 - Trabajo 2: Pipeline streaming end-to-end en Databricks

Maestria en Ciencia de Datos y Analitica - Universidad EAFIT - 2026-1
Curso: SI7006 Almacenamiento y Procesamiento de Grandes Datos
Fecha de entrega: 30 de abril de 2026

## Equipo

- Juan Jose Morales
- Sebastian Ruiz
- Santiago Molano
- Daniel Pareja

## Caso de uso

Monitoreo en tiempo real de ordenes en retail/e-commerce usando el
dataset `OnlineRetail.csv` como fuente de eventos simulados.

## Arquitectura

```text
OnlineRetail.csv
|
v
Productor Python  -->  /Volumes/.../stream_input/*.json
|
v
Auto Loader (Trigger.AvailableNow)
|
v
orders_bronze (Delta + metadata)
|
v
orders_silver (Delta limpio)
|
v
gold_kpi_ventana   gold_alertas_reorder (Delta)
|
v
AI/BI Dashboard de Databricks
```

## Stack

- Databricks Free Edition (serverless)
- Apache Spark Structured Streaming (PySpark)
- Delta Lake sobre Volumes de Unity Catalog
- Auto Loader (`cloudFiles`) con `Trigger.AvailableNow`
- AI/BI Dashboards de Databricks

## Estructura del repositorio

```text
si7006-trabajo2-streaming/
|-- README.md
|-- .gitignore
|-- notebooks/
|   |-- 00_setup_validacion.ipynb
|   |-- 01_bronze_ingesta.ipynb
|   |-- 02_silver_limpieza.ipynb
|   |-- 03_gold_kpis.ipynb
|   `-- 04_gold_alertas_reorder.ipynb
|-- productor/
|   `-- productor_eventos.ipynb
|-- queries/
|   |-- 01_revenue_total.sql
|   |-- 02_pedidos_totales.sql
|   |-- 03_unidades_vendidas.sql
|   |-- 04_revenue_por_minuto.sql
|   |-- 05_pedidos_por_minuto.sql
|   |-- 06_unidades_vendidas_por_minuto.sql
|   |-- 07_pedidos_guest_por_minuto.sql
|   |-- 08_alertas_por_nivel.sql
|   |-- 09_top_productos_menor_stock.sql
|   `-- 10_detalle_alertas.sql
|-- data/
|   `-- README.md
`-- docs/
    |-- informe_tecnico.md
    `-- declaraciones.md
```

## Como reproducir

### Prerrequisitos

1. Cuenta Databricks Free Edition con workspace activo.
2. `OnlineRetail.csv` descargado (ver `data/README.md`).

### Setup

1. En Catalog Explorer del workspace:
   - Crear schema `si7006_t2` en el catalogo `workspace`.
   - Crear 3 Volumes (Managed): `raw_data`, `stream_input`, `checkpoints`.
   - Subir `OnlineRetail.csv` al volume `raw_data`.
2. Importar los `.ipynb` de `notebooks/` y `productor/` como notebooks.
3. Ejecutar `00_setup_validacion` y verificar que las 4 celdas pasen.

### Corrida del pipeline

1. `01_bronze_ingesta` -> Run All. Dejar corriendo.
2. `productor_eventos` -> Run All en otra pestana inmediatamente despues.
3. Esperar a que ambos terminen (~4 min).
4. `02_silver_limpieza` -> Run All.
5. `03_gold_kpis` -> Run All.
6. `04_gold_alertas_reorder` -> Run All.

## Que construye la Gold

- `gold_kpi_ventana` materializa KPIs por ventanas de 1 minuto sobre
  `orders_silver`.
- Incluye `orders_count`, `units_sold`, `gross_revenue`,
  `avg_order_value`, `distinct_products`, `distinct_countries`
  y `guest_orders`.
- `gold_alertas_reorder` estima stock remanente por `stock_code`
  usando consumo acumulado y clasifica alertas `REORDER` y `CRITICO`.

## Etapas del proyecto

- Fase 0 - Setup y validacion
- Fase 1 - Productor + Bronze
- Fase 2 - Silver
- Fase 3 - Gold (KPIs y alertas)
- Fase 4 - Dashboard AI/BI
- Fase 5 - Informe + video

## Decisiones tecnicas clave

| Decision | Justificacion |
|---|---|
| Lotes de 50 eventos por archivo JSON | Evita el "small files problem" en Delta |
| Auto Loader (`cloudFiles`) | Manejo nativo de archivos incrementales y schema |
| Schema explicito | Documenta el contrato de la fuente |
| `Trigger.AvailableNow` + loop Python | Free Edition serverless no soporta triggers infinitos |
| `InvoiceDate` reescrito con `now()` en productor | Permite que las ventanas de Gold trabajen sobre tiempos coherentes |
| `dropDuplicatesWithinWatermark` 24h | Dedup stateful con estado acotado |
| Conservar filas guest (CustomerID null) | Evita subestimar el ingreso total en Gold |

## Declaraciones

Ver `docs/declaraciones.md`.
