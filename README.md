# SI7006 — Trabajo 2: Pipeline streaming end-to-end en Databricks

Maestría en Ciencia de Datos y Analítica — Universidad EAFIT — 2026-1
Curso: SI7006 Almacenamiento y Procesamiento de Grandes Datos

## Equipo

- Juan José Morales Guzmán — Tech Lead / Ingesta
- [Nombre 2] — Procesamiento / Streaming
- [Nombre 3] — Calidad y Eventos
- [Nombre 4] — Visualización y Documentación

## Caso de uso

Monitoreo en tiempo real de órdenes, inventario y alertas operativas
en retail/e-commerce, usando el dataset OnlineRetail.csv como fuente
de eventos simulados.

## Arquitectura

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

## Stack tecnológico

- **Plataforma:** Databricks Free Edition (serverless compute)
- **Procesamiento:** Apache Spark Structured Streaming (PySpark)
- **Almacenamiento:** Delta Lake sobre Volumes de Unity Catalog
- **Ingesta:** Auto Loader (`cloudFiles`) con `Trigger.AvailableNow`
- **Visualización:** AI/BI Dashboards de Databricks
- **Versionamiento:** Git

## Estructura del repositorio

```
si7006-trabajo2-streaming/
├── README.md                          # este archivo
├── .gitignore
├── notebooks/
│   ├── 00_setup_validacion.py         # validación de entorno
│   ├── 01_bronze_ingesta.py           # ingesta streaming a Bronze
│   ├── 02_silver_limpieza.py          # (Fase 2 - próxima)
│   ├── 03_gold_kpis.py                # (Fase 3 - próxima)
│   ├── 04_gold_alertas_reorder.py     # (Fase 3 - próxima)
│   └── 05_demo_delta_features.py      # (Fase 5 - próxima)
├── productor/
│   └── productor_eventos.py           # generador de eventos vivos
├── data/
│   └── README.md                      # cómo obtener OnlineRetail.csv
├── docs/
│   ├── informe_tecnico.md             # informe principal
│   ├── arquitectura.png               # diagrama (pendiente)
│   └── declaraciones.md               # uso de IA, fuentes, aporte
├── video/
│   └── guion_video.md                 # guion de la sustentación
└── evidencias/                        # capturas por fase
    ├── fase0/
    └── fase1/
```

## Cómo reproducir

### Prerrequisitos

1. Cuenta Databricks Free Edition con un workspace activo.
2. `OnlineRetail.csv` descargado localmente (ver `data/README.md`).

### Setup inicial (una vez por integrante)

1. En Databricks → Catalog Explorer:
   - Crear schema `si7006_t2` dentro del catálogo `workspace`.
   - Dentro del schema, crear 3 volumes (tipo Managed):
     - `raw_data`
     - `stream_input`
     - `checkpoints`
   - Subir `OnlineRetail.csv` al volume `raw_data`.

2. Importar los archivos `.py` de `notebooks/` y `productor/` como
   notebooks de Databricks.

3. Ejecutar `00_setup_validacion` y verificar que las 4 celdas pasen.

### Corrida del pipeline (Fase 1 actual)

1. Abrir `01_bronze_ingesta` en una pestaña.
2. Ejecutar celdas 1 a 4 (configuración).
3. **En otra pestaña**, abrir `productor_eventos`.
4. Ejecutar celdas 1 a 4 del productor (preparación).
5. (Opcional) Ejecutar celda 5 del productor para limpiar archivos previos.
6. Iniciar el loop de ingesta: ejecutar celda 5 de `01_bronze_ingesta`
   (queda corriendo).
7. **Inmediatamente después**, ejecutar celda 6 del productor
   (loop de producción).
8. Cuando ambos loops terminen, ejecutar celdas 6 y 7 de Bronze
   para validar.

## Estado actual del proyecto

- ✅ **Fase 0** — Setup y validación del entorno
- ✅ **Fase 1** — Generador de eventos + Ingesta Bronze
- ⏳ **Fase 2** — Capa Silver (pendiente)
- ⏳ **Fase 3** — Capa Gold con KPIs y alertas (pendiente)
- ⏳ **Fase 4** — Dashboard AI/BI (pendiente)
- ⏳ **Fase 5** — Robustez y Time Travel (pendiente)
- ⏳ **Fase 6** — Informe y video de sustentación (pendiente)

## Decisiones técnicas clave

| Decisión | Alternativa descartada | Justificación |
|---|---|---|
| Lotes de N eventos por archivo JSON | 1 evento por archivo | Evita el "small files problem" en Delta |
| Auto Loader (`cloudFiles`) | `readStream.format("json")` | Mejor escalabilidad y manejo de schema |
| Schema explícito | Inferencia | Documenta el contrato y mejora performance |
| `Trigger.AvailableNow` + loop Python | `processingTime` continuo | Free Edition serverless no soporta triggers infinitos |
| Sobrescribir `InvoiceDate` con `now()` en productor | Conservar fechas originales (2010-2011) | Permite que ventanas tumbling/sliding trabajen sobre tiempos coherentes con la demo |

## Fecha de entrega

**30 de abril de 2026** — Modo de entrega: Asignaciones de EAFIT Interactiva.

## Declaraciones

Ver `docs/declaraciones.md` para:
- Uso de IA generativa
- Fuentes externas y código reutilizado
- Aporte individual de cada integrante
