# SI7006 — Trabajo 2
## Pipeline streaming end-to-end en Databricks: monitoreo de órdenes en retail

**Equipo:**
- Juan José Morales Guzmán
- [Nombre 2]
- [Nombre 3]
- [Nombre 4]

**Fecha:** 30 de abril de 2026
**Curso:** SI7006 — Almacenamiento y Procesamiento de Grandes Datos
**Universidad:** EAFIT — Maestría en Ciencia de Datos y Analítica — Cohorte 2026-1

---

## 1. Resumen ejecutivo

*[Pendiente — completar al cierre del proyecto. 1 párrafo describiendo
qué se construyó y qué demuestra.]*

## 2. Contexto y caso de uso

*[Pendiente — completar al cierre. Por qué retail/e-commerce, qué
pregunta de negocio responde el pipeline.]*

## 3. Arquitectura de referencia

### 3.1 Diagrama

*[Insertar `arquitectura.png` cuando esté listo.]*

```
OnlineRetail.csv (estático)
        │
        ▼
   Productor Python  ──────►  /Volumes/.../stream_input/*.json
                                       │
                                       ▼
                          Auto Loader (Trigger.AvailableNow)
                                       │
                                       ▼
                          orders_bronze (Delta, raw + metadata)
                                       │
                                       ▼
                          orders_silver (Delta, limpio)
                                       │
                                       ▼
                  gold_kpi_ventana   gold_alertas_reorder (Delta)
                                       │
                                       ▼
                          AI/BI Dashboard de Databricks
```

### 3.2 Componentes

| Componente | Tecnología | Propósito |
|---|---|---|
| Fuente de datos | OnlineRetail.csv (UCI) | Dataset de e-commerce con ~541k transacciones |
| Generador de eventos | Python + pandas en notebook | Simula órdenes llegando en vivo escribiendo lotes JSON |
| Zona de aterrizaje | Volume Unity Catalog `stream_input/` | Directorio donde caen los archivos JSON |
| Ingesta streaming | Spark Structured Streaming + Auto Loader | Detecta archivos nuevos y los procesa incrementalmente |
| Bronze | Delta Lake (Unity Catalog) | Datos crudos + metadata de trazabilidad |
| Silver | Delta Lake | Datos limpios, deduplicados, enriquecidos |
| Gold | Delta Lake | KPIs por ventana + alertas operativas |
| Visualización | AI/BI Dashboards de Databricks | Tableros refrescados sobre tablas Gold |

### 3.3 Decisiones de diseño

*[Esta sección crece con cada fase. Lo que ya está documentado:]*

| Decisión | Alternativa descartada | Justificación |
|---|---|---|
| Dataset OnlineRetail | API externa, Bluesky, Kafka | Mencionado explícitamente en el enunciado, sin credenciales, conocido por el curso |
| Lotes de N eventos por JSON | 1 evento por archivo | Evita el "small files problem" en Delta |
| Auto Loader (`cloudFiles`) | `readStream.format("json")` | Optimizado para archivos en directorio, manejo de schema robusto |
| Schema explícito | Inferencia | Documenta el contrato y mejora performance |
| `Trigger.AvailableNow` + loop Python | `processingTime` continuo | Free Edition serverless no soporta triggers infinitos |
| Sobrescribir `InvoiceDate` con `now()` | Conservar fechas originales (2010-2011) | Permite que ventanas tumbling/sliding trabajen sobre tiempos coherentes con la demo |

---

## 4. Implementación técnica

### 4.1 Setup del entorno (Fase 0)

#### Estructura de Unity Catalog

Se creó una estructura jerárquica en el catálogo `workspace` (catálogo
por defecto en Databricks Free Edition):

```
workspace
└── schema: si7006_t2
    ├── volume: raw_data       (CSV original)
    ├── volume: stream_input   (archivos JSON del productor)
    └── volume: checkpoints    (estado de los queries streaming)
```

Los Volumes de Unity Catalog son la forma recomendada en Free Edition
para almacenar datos no tabulares (CSV, JSON, archivos crudos), ya que
se acceden vía paths normales del filesystem (`/Volumes/...`) tanto
desde código Python nativo como desde Spark.

#### Validación del entorno

El notebook `00_setup_validacion.py` valida en 4 celdas:

1. Versiones de Python, PySpark y Delta Lake.
2. Definición centralizada de variables (catálogo, schema, paths, tablas).
3. Lectura del CSV con encoding correcto (Latin-1) y conteo de filas
   (~541,909).
4. Creación del schema y test de escritura de una tabla Delta dummy.

#### Limitaciones identificadas en Free Edition

- No expone el wizard completo de "Lakeflow Connect" para crear
  pipelines de ingesta declarativos por interfaz web.
- El compute serverless no permite triggers de streaming infinitos
  (`processingTime`, `continuous`).
- Tiene timeout de inactividad: si un stream se deja corriendo sin
  datos por mucho tiempo, el cluster se apaga.

Estas limitaciones se manejan con las decisiones de diseño documentadas
en las siguientes secciones.

---

### 4.2 Generación de eventos vivos y capa Bronze (Fase 1)

#### Generador de eventos

Implementado en `productor/productor_eventos.py`. El productor:

1. Carga `OnlineRetail.csv` una sola vez a memoria con pandas, usando
   encoding Latin-1 y especificación explícita de tipos (incluyendo
   nullables `Int64` para `Quantity` y `CustomerID`).
2. Mezcla el dataset aleatoriamente (`random_state=42`) para que cada
   lote contenga órdenes variadas en lugar de ordenadas por fecha.
3. En un loop controlado, toma un slice de N eventos, sobrescribe la
   columna `InvoiceDate` con el timestamp actual, y los serializa a un
   archivo JSON Lines (NDJSON) en el volume `stream_input/`.
4. Espera N segundos entre lotes para simular el ritmo de un sistema
   de e-commerce real.

**Configuración usada para validar Fase 1:**
- Eventos por lote: 50
- Segundos entre lotes: 5
- Lotes totales: 30
- Total de eventos generados: 1,500
- Duración: 2.5 minutos

**Decisión clave:** se eligieron lotes de 50 eventos en lugar de
eventos individuales para evitar generar miles de archivos pequeños
(el "small files problem" degrada drásticamente el performance de
Delta Lake al hacer queries posteriores). Este es el patrón que usan
en producción servicios como Kinesis Firehose o Auto Loader sobre S3.

#### Ingesta Bronze con Auto Loader

Implementada en `notebooks/01_bronze_ingesta.py`. El stream:

1. Configura un `readStream` con format `cloudFiles` (Auto Loader),
   apuntando al volume `stream_input/`, con schema explícito y
   `schemaLocation` para que Auto Loader persista metadata del schema.
2. Enriquece cada registro con 4 columnas de metadata de auditoría:
   - `ingested_at`: `current_timestamp()` del momento de ingesta.
   - `source_file`: nombre del archivo de origen
     (`_metadata.file_path`).
   - `source_file_size`: tamaño del archivo origen.
   - `source_file_modtime`: timestamp de modificación del archivo.
3. Escribe a la tabla Delta `workspace.si7006_t2.orders_bronze`
   gestionada por Unity Catalog.

#### Patrón micro-batch incremental

**Problema encontrado:** el primer intento usó
`trigger(processingTime="10 seconds")`, esperando un stream continuo.
El compute serverless de Databricks Free Edition rechazó este trigger
con el error:

```
[INFINITE_STREAMING_TRIGGER_NOT_SUPPORTED]
Trigger type ProcessingTime is not supported for this cluster type.
Use a different trigger type e.g. AvailableNow, Once.
```

**Solución adoptada:** se reemplazó por `trigger(availableNow=True)`,
que procesa todos los archivos nuevos disponibles y termina el query.
Para simular un stream "siempre activo", se envolvió el writeStream
en un loop Python que ejecuta una pasada cada N segundos.

Este patrón se conoce como **micro-batch incremental** y es ampliamente
usado en producción cuando la latencia aceptable es del orden de
minutos (no segundos). Mantiene todas las garantías de Delta Lake:

- **ACID**: cada pasada es transaccional.
- **Exactly-once**: el checkpoint registra qué archivos ya se
  procesaron; reejecuciones son idempotentes.
- **Schema enforcement**: rechaza archivos que no cumplan el schema.

**Configuración usada:**
- 20 iteraciones × 12 segundos = 4 minutos de cobertura.
- Cobertura amplia respecto al productor (2.5 min) para garantizar
  que el último lote sea procesado.

#### Resultados validados en Fase 1

| Métrica | Valor |
|---|---|
| Archivos generados por el productor | 30 |
| Archivos detectados por Auto Loader | 30 |
| Eventos en `orders_bronze` | 4,500 (acumulado de 3 corridas de validación) |
| Commits Delta registrados | 3 (uno por pasada con datos) |
| Schema de la tabla Bronze | 8 columnas de negocio + 4 de auditoría |
| Errores de schema | 0 |
| Errores de duplicación | 0 |

#### Aprendizajes clave de Fase 1

1. **`query.lastProgress` retorna `None` cuando no hay archivos
   nuevos**, no un dict con `numInputRows: 0`. Esto inicialmente
   confundió el reporte del loop. La fuente de verdad es siempre el
   conteo de la tabla, no el estado del query.
2. **Cada query streaming necesita su propio `checkpointLocation` y
   `schemaLocation` únicos.** Reusar paths entre queries distintos
   corrompe el estado.
3. **Los Volumes de Unity Catalog son el path correcto para escribir
   archivos arbitrarios** desde Python nativo en Free Edition. DBFS
   clásico (`dbfs:/`) tiene limitaciones en serverless.
4. **El `mergeSchema=true` no es opcional**: si en el futuro se añade
   una columna a la fuente, sin esta opción el stream falla.

---

### 4.3 Capa Silver: limpieza y enriquecimiento (Fase 2)

*[Pendiente — Fase 2.]*

### 4.4 Capa Gold: KPIs, ventanas y alertas (Fase 3)

*[Pendiente — Fase 3.]*

### 4.5 Visualización en AI/BI Dashboards (Fase 4)

*[Pendiente — Fase 4.]*

### 4.6 Características Delta: ACID, schema enforcement, time travel (Fase 5)

*[Pendiente — Fase 5.]*

---

## 5. Resultados y demostración

*[Pendiente — completar con capturas y métricas finales.]*

## 6. Limitaciones del Free Tier y workarounds

| Limitación | Impacto | Workaround adoptado |
|---|---|---|
| No soporta triggers `processingTime`/`continuous` | No se puede tener stream "siempre activo" | Loop Python externo con `Trigger.AvailableNow` |
| Wizard de Lakeflow Connect limitado | No se pudo crear pipeline Bronze por UI | Implementación programática en PySpark |
| Timeout de inactividad en serverless | Stream muere si se deja sin datos mucho tiempo | Demo se corre de seguido sin pausas largas |
| Sin Unity Catalog completo (sin algunos comandos avanzados de gobernanza) | Limita demostración de gobernanza | Se documenta la limitación; se demuestran las funciones que sí están disponibles |

## 7. Conclusiones

*[Pendiente — completar al cierre.]*

## 8. Reproducibilidad

Ver `README.md` del repositorio para instrucciones paso a paso.

## 9. Declaraciones

Ver `docs/declaraciones.md`.

## 10. Referencias

- Material del curso SI7006 (sesiones 1 a 6).
- Repositorio oficial del curso: https://github.com/si7006eafit/si7006-261
- Documentación de Databricks Auto Loader:
  https://docs.databricks.com/en/ingestion/auto-loader/index.html
- Documentación de Delta Lake:
  https://docs.delta.io/latest/index.html
- Dataset OnlineRetail (UCI ML Repository):
  https://archive.ics.uci.edu/dataset/352/online+retail
