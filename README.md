# omni-rag

**Plataforma de RAG para soporte y postventa retail** — responde preguntas usando
**solo** documentos indexados (manuales, políticas, FAQs), con **citas verificables**
y **sin alucinar**. Motor de IA **100% local** (Ollama): ningún dato sale de tu
infraestructura.

> Proyecto propio de **Mario A. Cabral**, ingenierizado a estándar de producción
> (API, bases de datos, tests, contenedores, observabilidad, CI/CD y despliegue en
> la nube). Pensado para el dominio de **soporte / postventa omnicanal**.

![CI](https://github.com/macpampa2026/omni-rag/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ¿Por qué existe?

Un asistente de soporte que **inventa** un plazo de garantía o una política de
devolución es peor que no tener asistente. omni-rag responde **anclado** a los
documentos oficiales que le cargues y **cita la fuente** de cada afirmación; si la
respuesta no está en los documentos, lo dice — no la inventa.

## ¿Para qué sirve?

Imaginá el mostrador de una tienda o un call center. Un cliente pregunta:

> *"¿Este aire acondicionado tiene garantía y cuántos días tengo para devolverlo
> si no me convence?"*

En vez de buscar en una carpeta o dejar al cliente esperando, alguien —un
empleado, o directamente un chatbot— le pregunta a omni-rag y obtiene:

> *"Los productos electrónicos tienen 6 meses de garantía contra fallas. Tenés
> 30 días corridos para devolverlo sin uso, con el ticket [1]."*

…y con ese **[1]** puede ver de qué documento oficial salió la respuesta. Si la
pregunta no está en los documentos, responde **"La información disponible no
cubre ese punto"** en lugar de inventar.

**Casos de uso típicos:**

- **Soporte y postventa** — garantías, devoluciones, envíos, financiación.
- **Chatbot de atención al cliente** que solo contesta con información oficial.
- **Capacitación / onboarding** — el personal consulta procedimientos al instante.
- **Manuales técnicos** — *"¿cómo reseteo el modelo X?"*.
- Fuera del retail: estudios jurídicos, clínicas, bancos, seguros, RR. HH.

### ¿Cómo funciona? (en simple)

```mermaid
flowchart LR
    U["Empleado o cliente hace una pregunta"] --> API["omni-rag (API)"]
    D[("Documentos oficiales: manuales, politicas, FAQs")] --> R
    API --> R["1 - Busca los fragmentos relevantes"]
    R --> G["2 - El LLM local redacta SOLO con eso"]
    G --> A["3 - Respuesta + cita, o 'no lo cubre'"]
```

El valor no es solo *responder*: es **no mentir**. Un asistente que se inventa un
plazo de garantía es peor que no tener nada. omni-rag responde **anclado a los
documentos y citando la fuente**, y es **100% local** (los datos no salen de tu
infraestructura).

## Arquitectura (resumen)

```mermaid
flowchart TB
    U["Usuario / cliente"]
    OLL["Ollama en el host - LLM + embeddings"]

    subgraph stack["Stack desplegable (docker compose / Kubernetes)"]
        GW["gateway - Go - salud del sistema"]
        API["api - FastAPI - RAG por capas"]
        PG[("PostgreSQL + pgvector")]
        RD[("Redis - cache de embeddings")]
        PR["Prometheus"]
        GF["Grafana - dashboard"]
    end

    U --> GW
    U --> API
    GW -->|consulta /health/ready| API
    API -->|SQL + busqueda vectorial| PG
    API -->|cache| RD
    API -->|embeddings + generacion| OLL
    PR -->|scrapea /metrics| API
    GF --> PR
```

Capas del servicio API (`services/api/app/`):

| Capa | Responsabilidad |
|---|---|
| `api/` | Routers HTTP (health, documents, ask) + auth por API key |
| `services/` | chunking · embeddings (Ollama) · vector store · recuperación · RAG |
| `models/` | Schemas Pydantic (contrato de la API) |
| `config.py` · `logging_conf.py` | Configuración por entorno · logging JSON |

Decisiones de diseño documentadas en [`docs/adr/`](docs/adr/).

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/health` | Liveness |
| `GET` | `/health/ready` | Readiness (comprueba Ollama, reporta el índice) |
| `POST` | `/documents` | Ingesta de texto |
| `POST` | `/documents/pdf` | Ingesta de PDF (indexa por página) |
| `GET` | `/documents` | Lista documentos indexados |
| `POST` | `/ask` | Pregunta (RAG con citas) |
| `GET` | `/docs` | Documentación OpenAPI (Swagger UI) |

## Cómo correrlo (local)

Requiere **Python 3.11+** y **[Ollama](https://ollama.com)** corriendo con los modelos:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

Luego:

```bash
cd services/api
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Abrí **http://localhost:8000/docs**.

### Ejemplo

```bash
# Ingestar una política
curl -X POST http://localhost:8000/documents -H "Content-Type: application/json" -d "{\"doc_id\":\"devoluciones\",\"title\":\"Politica de devoluciones\",\"text\":\"El cliente tiene 30 dias corridos para devolver un producto sin uso, con el ticket de compra.\"}"

# Preguntar
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\":\"Cuantos dias tengo para devolver?\"}"
```

## Base de datos (PostgreSQL + pgvector)

Por defecto omni-rag usa un índice en memoria (ideal para probar). Para uso real,
puede usar **PostgreSQL con la extensión [pgvector](https://github.com/pgvector/pgvector)**
como almacén **relacional + vectorial**. Solo hay que definir `OMNIRAG_DATABASE_URL`
(por ejemplo, una base gratis de [Neon](https://neon.tech)):

```bash
cd services/api
# 1) Poné tu cadena de conexión en services/api/.env (driver +psycopg):
#    OMNIRAG_DATABASE_URL=postgresql+psycopg://USER:PASS@HOST/DB?sslmode=require
# 2) Creá el esquema (extensión vector + tablas) con Alembic:
alembic upgrade head
# 3) Arrancá la API: /health/ready ahora reporta "store": "postgres:up"
uvicorn app.main:app --reload
```

**Esquema** (migración `alembic/versions/0001_initial.py`):

- `documents(doc_id, title)` — un registro por documento.
- `chunks(id, doc_id → documents, page, text, embedding vector(768))` — fragmentos,
  con índice **HNSW** para búsqueda por distancia coseno.

Si `OMNIRAG_DATABASE_URL` no está definida, se usa el índice en memoria (M1). El
mismo `VectorStore` (interfaz) permite intercambiar backends sin tocar la lógica.

## Docker (stack completo)

Para levantar **todo el stack** (API + PostgreSQL con pgvector + Redis) con un
solo comando, sin instalar nada más que Docker:

```bash
docker compose up --build
```

Arranca tres servicios:

- **db** — PostgreSQL con la extensión `pgvector` (imagen `pgvector/pgvector`).
- **redis** — cache de embeddings de consultas.
- **api** — el servicio FastAPI: corre las migraciones de Alembic y levanta en el puerto 8000.

El motor de IA (Ollama) corre en tu máquina (host); el contenedor `api` lo alcanza
vía `host.docker.internal`. Abrí **http://localhost:8000/docs**.

## Observabilidad (Prometheus + Grafana)

La API expone métricas en formato Prometheus en **`/metrics`**: conteo y latencia de
requests HTTP, consultas RAG, documentos ingestados y aciertos/fallos del cache de
embeddings. El stack de `docker compose` incluye **Prometheus** (que scrapea la API) y
**Grafana** con un **dashboard provisionado**:

- Prometheus → **http://localhost:9090**
- Grafana (dashboard *"omni-rag — Observabilidad"*) → **http://localhost:3000** (login anónimo)

Configuración en `deploy/prometheus/` y `deploy/grafana/provisioning/`.

## Gateway (microservicio en Go)

Además del servicio principal en Python, hay un pequeño **microservicio en Go**
(`services/gateway/`) que **agrega la salud del sistema**: expone su propia
liveness y consulta la API de Python para reportar un estado combinado. Demuestra
comunicación entre servicios en distintos lenguajes (**Go ↔ Python**).

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/healthz` | Liveness del gateway |
| `GET` | `/status` | Estado combinado: gateway + API (consulta `/health/ready`) |

Corre solo (con la API de Python en el puerto 8000):

```bash
cd services/gateway
go run .            # escucha en :9000
curl localhost:9000/status
```

También forma parte del stack de `docker compose` (puerto 9000), alcanzando a la
API por su nombre de servicio (`http://api:8000`).

## Kubernetes (despliegue local)

Los manifiestos en [`deploy/k8s/`](deploy/k8s/) despliegan **todo el stack** en un
cluster de Kubernetes (probado en el que trae Docker Desktop): **postgres** (pgvector)
con PVC, **redis**, **api** (con las migraciones en un *initContainer*, probes de
liveness/readiness, límites de recursos y un **HorizontalPodAutoscaler**) y **gateway**,
cada uno con su Service.

```bash
# 1) Construir las imágenes locales que usa el cluster:
docker build -t omni-rag-api:local services/api
docker build -t omni-rag-gateway:local services/gateway
# 2) Desplegar:
kubectl apply -f deploy/k8s/
kubectl get pods -n omni-rag
# 3) Acceder al API:
kubectl port-forward -n omni-rag svc/api 8000:8000   # -> http://localhost:8000/docs
```

## Tests

```bash
cd services/api
pytest
```

## Hoja de ruta

- [x] **M1** — API core RAG (FastAPI, capas, health/documents/ask, tests base)
- [x] **M2** — PostgreSQL + pgvector (almacén relacional + vectorial, migraciones Alembic)
- [x] **M3** — Tests + CI (ruff + pytest en GitHub Actions)
- [x] **M4** — Docker + docker-compose (API + Postgres/pgvector + Redis)
- [x] **M5** — Microservicio en Go (gateway de estado; comunicación Go ↔ Python)
- [x] **M6** — Observabilidad (métricas Prometheus + dashboard Grafana provisionado)
- [x] **M7** — Manifiestos de Kubernetes (stack completo, verificado en cluster local) · *deploy en Render: opcional*
- [ ] **M8** — Vitrina y pitch

## Licencia

MIT — ver [LICENSE](LICENSE).
