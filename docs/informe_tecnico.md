# SI7006 — Trabajo 2

## Pipeline streaming end-to-end en Databricks: monitoreo de órdenes en retail

Equipo:
- Juan José Morales
- Sebastian Ruiz
- Santiago Molano
- Daniel Pareja

Fecha: 30 de abril de 2026
Curso: SI7006 — Almacenamiento y Procesamiento de Grandes Datos
Universidad EAFIT — Maestría en Ciencia de Datos y Analítica — Cohorte 2026-1

## 1. Resumen ejecutivo



## 2. Caso de uso

Monitoreo en tiempo real de órdenes en retail/e-commerce. El pipeline
ingesta eventos de venta de forma continua, los limpia y enriquece, y
produce KPIs por ventana de tiempo y alertas de reorden de inventario.
La fuente es el dataset `OnlineRetail.csv` (UCI), un histórico real de
~541,909 transacciones.

## 3. Arquitectura

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

### Componentes

| Componente | Tecnología | Propósito |
|---|---|---|
| Fuente | OnlineRetail.csv | Dataset histórico de e-commerce |
| Productor | Python + pandas | Simula órdenes vivas en lotes JSON |
| Aterrizaje | Volume `stream_input/` | Directorio donde caen los JSON |
| Ingesta | Auto Loader + Structured Streaming | Detección incremental de archivos |
| Bronze | Delta Lake | Datos crudos + metadata de auditoría |
| Silver | Delta Lake | Datos limpios, deduplicados, enriquecidos |
| Gold | Delta Lake | KPIs por ventana y alertas |
| Visualización | AI/BI Dashboards | Tableros sobre tablas Gold |

### Decisiones de diseño

| Decisión | Justificación |
|---|---|
| OnlineRetail.csv como fuente | Mencionado en el enunciado, sin credenciales |
| Lotes de 50 eventos por JSON | Evita el "small files problem" en Delta |
| Auto Loader (`cloudFiles`) | Manejo nativo de archivos incrementales y schema |
| Schema explícito | Documenta el contrato |
| `Trigger.AvailableNow` + loop Python | Free Edition serverless no soporta triggers infinitos |
| Reescribir `InvoiceDate` con `now()` | Permite que las ventanas de Gold trabajen sobre tiempos coherentes con la demo |
| `dropDuplicatesWithinWatermark` 24h | Dedup stateful con estado acotado |
| Conservar filas guest (CustomerID null) | Evita subestimar el ingreso total |

## 4. Implementación

### 4.1 Setup del entorno

Estructura creada en Unity Catalog:

workspace
└── si7006_t2
├── raw_data       (CSV original)
├── stream_input   (JSON del productor)
└── checkpoints    (estado de los queries)

Los Volumes son la forma recomendada en Free Edition para almacenar
datos no tabulares.

El notebook `00_setup_validacion` valida en 4 celdas: versiones del
stack, configuración de variables, lectura del CSV con encoding
Latin-1 (~541,909 filas), y creación del schema en Unity Catalog.

### 4.2 Productor de eventos y capa Bronze

#### Productor

`productor_eventos.py` carga el CSV en memoria con encoding Latin-1,
mezcla el dataset (`random_state=42`), y en un loop genera lotes de
50 eventos cada 5 segundos. Cada lote sobrescribe `InvoiceDate` con
el timestamp actual y se escribe como archivo JSON Lines en
`stream_input/`.

Configuración de la corrida: 30 lotes × 50 eventos = 1,500 eventos
en 2.5 minutos.

#### Bronze

`01_bronze_ingesta.py` configura un `readStream` con format
`cloudFiles`, schema explícito y `schemaLocation` persistente.
Enriquece cada registro con 4 columnas: `ingested_at`,
`source_file`, `source_file_size`, `source_file_modtime`.

#### Patrón micro-batch incremental

El primer intento usó `trigger(processingTime="10 seconds")` y el
serverless lo rechazó con `INFINITE_STREAMING_TRIGGER_NOT_SUPPORTED`.
Se sustituyó por `trigger(availableNow=True)` envuelto en un loop
Python que ejecuta una pasada cada 12 segundos durante 20 iteraciones.

Este patrón mantiene las garantías Delta:
- ACID: cada pasada es transaccional.
- Exactly-once: el checkpoint registra qué archivos se procesaron.
- Schema enforcement: rechaza archivos que no cumplan el schema.

### 4.3 Capa Silver

`02_silver_limpieza.py` lee en streaming desde `orders_bronze` con
`readStream.format("delta").table()`, aplica filtros y enriquecimiento,
y escribe a `orders_silver` con el mismo patrón loop + AvailableNow
de Bronze.

#### Filtros de calidad

- Cancelaciones: `InvoiceNo` que comienza con `"C"`.
- Cantidades inválidas: `Quantity <= 0`.
- Precios inválidos: `UnitPrice <= 0`.
- `StockCode` o `InvoiceDate` nulos o vacíos.

#### Enriquecimiento

- `event_time`: timestamp parseado desde `InvoiceDate`. Es la columna
  canónica para watermarks y ventanas en Gold.
- `total_amount = round(Quantity * UnitPrice, 2)`: ingreso por línea.
- `is_guest`: flag booleano cuando `CustomerID` es null.
- `customer_id_imputed`: `CustomerID` o `"GUEST"` si es null.

Las filas guest representan ~26% del dataset. Se conservan en lugar
de descartarlas para no subestimar el ingreso total en los KPIs de
Gold.

#### Deduplicación con watermark

`dropDuplicatesWithinWatermark` por `(InvoiceNo, StockCode)` con
watermark de 24 horas sobre `event_time`.

#### Garantías Delta validadas

- **Exactly-once / Idempotencia**: ejecutar el loop sin datos nuevos
  produce delta = 0 filas. El checkpoint registra correctamente el
  offset comprometido.
- **Time Travel**: `DESCRIBE HISTORY` y `VERSION AS OF` operativos.
  La tabla muestra commits separados de `CREATE TABLE` (v0) y
  `STREAMING UPDATE` (v1+).
- **Schema Enforcement**: append con columna adicional rechazado con
  `DELTA_METADATA_MISMATCH`.

#### Resultados validados

| Indicador | Valor |
|---|---|
| Filas en Silver | 2,927 |
| Filas guest | 771 |
| Filas con CustomerID | 2,156 |
| Suma de control `total_amount` | $56,489.82 |
| Países distintos | 32 |
| Productos distintos | 1,464 |
| Duplicados de clave de negocio | 0 |

### 4.4 Capa Gold: KPIs y alertas



### 4.5 Visualización en AI/BI Dashboards



## 5. Resultados y demostración



## 6. Limitaciones del Free Tier

| Limitación | Alternativa |
|---|---|
| No soporta triggers `processingTime`/`continuous` | Loop Python con `Trigger.AvailableNow` |
| Wizard de Lakeflow Connect limitado | Implementación programática en PySpark |
| Timeout de inactividad en serverless | Demo se corre sin pausas largas |

## 7. Conclusiones



## 8. Referencias

- Material del curso SI7006 (sesiones 1 a 6).
- Repositorio del curso: https://github.com/si7006eafit/si7006-261
- OnlineRetail (UCI): https://archive.ics.uci.edu/dataset/352/online+retail