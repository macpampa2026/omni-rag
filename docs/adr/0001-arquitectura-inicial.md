# ADR 0001 — Arquitectura inicial de omni-rag

- **Estado:** Aceptado
- **Fecha:** 2026-08-08

## Contexto

Partimos de una demo de RAG local monolítica (un `server.py` con la librería
estándar). Queremos evolucionarla a un servicio estilo producción: testeable,
observable, desplegable en la nube y con bases de datos reales, sin perder la
propiedad clave de **no alucinar** (responder solo con el contexto y citar).

## Decisiones

1. **FastAPI** como framework del servicio HTTP: tipado con Pydantic v2, docs
   OpenAPI automáticas, y buen soporte de inyección de dependencias.
2. **Arquitectura por capas** dentro del servicio API:
   - `api/` — routers HTTP (sin lógica de negocio).
   - `services/` — lógica: chunking, embeddings, recuperación, RAG.
   - `models/` — schemas Pydantic (contrato público).
   - `config.py` / `logging_conf.py` — configuración y logging transversales.
3. **Abstracción del almacén de vectores** (`VectorStore` como `Protocol`).
   Hoy: `InMemoryVectorStore` (JSON). En el M2: `PgVectorStore`
   (PostgreSQL + pgvector) **sin tocar la lógica de negocio**.
4. **Motor de IA local** (Ollama): embeddings con `nomic-embed-text`,
   generación con `qwen2.5:7b`. Ningún dato sale de la infraestructura.
5. **Objetos de larga vida en el lifespan** y expuestos vía `app.state`, para
   poder reemplazarlos por dobles de prueba en los tests.
6. **Logging estructurado en JSON** desde el día uno (preparado para M6).

## Consecuencias

- El código queda listo para intercambiar el backend de datos (M2) y para
  contenerizar (M4) y desplegar (M7) sin reescrituras.
- Costo: más archivos y ceremonia que un script único, a cambio de
  testabilidad y evolución.

## Hoja de ruta (milestones)

M1 API core · M2 PostgreSQL+pgvector+Redis · M3 Tests+CI · M4 Docker ·
M5 microservicio Go · M6 observabilidad · M7 nube+K8s · M8 vitrina.
