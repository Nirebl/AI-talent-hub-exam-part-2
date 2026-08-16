# Support Ticket AI

Минимальный PoC AI/ML-системы для автоматизации обработки тикетов поддержки крупного онлайн-сервиса.

Система принимает обращение из chat/email/web/mobile, выполняет быстрые классификацию и risk-routing, сохраняет решение для аудита и отправляет безопасные типовые обращения в асинхронный retrieval + LLM pipeline. Рискованные, low-confidence и содержащие PII обращения не закрываются автоматически и переводятся оператору.

## Зачем это бизнесу

При 200k тикетов в день и стоимости ручной обработки около 150 ₽ даже частичная автоматизация даёт заметный эффект. Если безопасно автоматизировать 10–20% общего потока, это эквивалентно освобождению операторской мощности на 20–40k тикетов в день, или 3–6 млн ₽/день по указанной стоимости обработки до учёта стоимости LLM, инфраструктуры и эффекта reopen. При этом цель системы не максимизировать automation rate любой ценой: CSAT, reopen rate и SLA являются guardrails. Основная ценность — быстрее закрывать типовые обращения и оставлять операторское время сложным и рискованным случаям.

## Что реализовано

- FastAPI API: `POST /tickets`, `GET /tickets/{id}`, `/health`, `/ready`, `/metrics`
- deterministic baseline classifier + confidence
- PII detection
- deterministic `RiskPolicy`: риск не делегируется LLM
- human/LLM routing
- TF-IDF retrieval по локальной knowledge base
- retrieval audit: `document_id`, `rank`, `score`, retriever version, run id
- mock generator и локальный Qwen adapter
- deterministic output safety checks
- idempotency по `(channel, external_id)` и при повторной доставке generation task
- local async queue и Celery/Redis adapter
- in-memory и SQLAlchemy/PostgreSQL persistence adapters
- Docker Compose: API + PostgreSQL + Redis + Celery worker
- optional Docker Qwen worker build
- 90 unit/integration/E2E tests
- HTTP load-test script

## Главный архитектурный принцип

**LLM не находится на hot path.** Классификация, PII-check и routing должны укладываться в ориентир до 500 ms; генерация ответа выполняется асинхронно.

```text
client
  |
  v
FastAPI
  |-- classifier
  |-- PII detector
  |-- RiskPolicy
  |-- persist Ticket + Decision
  |
  |-- HUMAN
  |
  `-- Redis/Celery --> worker --> retrieval --> LLM --> safety --> persist Answer
```

## Почему такой стек

Стек выбран под свойства задачи, а не ради полноты инфраструктуры: FastAPI даёт тонкий typed ingress; PostgreSQL — долговременный audit/source of truth; Redis + Celery отделяют нестабильную LLM latency от synchronous hot path; TF-IDF является дешёвым и объяснимым retrieval baseline; Qwen используется как optional local `AnswerGenerator`, чтобы показать реальный LLM path без обязательной внешней API-зависимости. RiskPolicy и output safety остаются deterministic, потому что эти решения должны быть auditable и не зависеть от генеративной модели. Подробнее — в [Architecture](docs/architecture.md) и [ML/LLM design](docs/ml.md).

## Быстрый локальный запуск

```bash
pip install -r requirements.txt
```

PowerShell:

```powershell
$env:QUEUE_BACKEND="local"
$env:PERSISTENCE_BACKEND="memory"
$env:LLM_BACKEND="mock"

python -m uvicorn support_ai.infrastructure.api.app:app `
  --app-dir src `
  --host 0.0.0.0 `
  --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### Happy path

```json
{
  "external_id": "web-001",
  "channel": "web",
  "text": "Как поменять пароль?",
  "user_id": "user-001",
  "metadata": {
    "thread_id": "thread-001",
    "language": "ru",
    "client": "web",
    "app_version": "1.0.0"
  }
}
```

Ожидаемый initial decision:

```text
status=pending
route=llm
category=account
reason=safe_automation
```

После async generation `GET /tickets/{ticket_id}` возвращает `status=resolved`, retrieval audit и отправленный answer.

### Fallback/risky path

Например:

```text
С моей карты списали деньги без моего согласия
```

Ожидаемо:

```text
route=human
risk_level=high
reason=high_risk_category
answer=null
```

Тот же fallback применяется для PII, low confidence, недостаточного retrieval context, unsafe generation и недоступного LLM.

## Локальный Qwen

```bash
pip install -r requirements-llm.txt
```

```powershell
$env:QUEUE_BACKEND="local"
$env:PERSISTENCE_BACKEND="memory"
$env:LLM_BACKEND="qwen"
$env:QWEN_MODEL_ID="Qwen/Qwen3-4B-Instruct-2507"
$env:QWEN_LOAD_IN_4BIT="true"
```

Qwen загружается при startup runtime, а не внутри первого HTTP request.

## Docker Compose

Распределённый PoC без GPU-зависимости:

```bash
docker compose up --build
```

Он поднимает:

```text
FastAPI + PostgreSQL + Redis + Celery worker
```

Optional Qwen worker:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.qwen.yml \
  up --build
```

Для Qwen worker используется `concurrency=1`, NVIDIA GPU reservation и persistent Hugging Face cache. Knowledge base path задаётся runtime-переменной и не зависит от расположения установленного Python package.

## Реализация vs target design

| Часть | В PoC | Целевая система |
|---|---|---|
| Classification | deterministic rules | обученная low-latency classifier model |
| Retrieval | TF-IDF + cosine | semantic embeddings + vector search |
| Generation | mock / local Qwen | отдельный controlled inference service/API |
| Persistence | memory / SQLAlchemy | HA PostgreSQL + migrations |
| Queue | local thread / Celery | durable broker + retries/DLQ/outbox |
| Metrics | in-memory `/metrics` | Prometheus/OpenTelemetry + dashboards |
| Deployment | local / Docker Compose | horizontally scalable services |

## Проверка

```bash
pytest -q
```

Текущий suite: **90 tests**.

Локальный hot-path benchmark (`memory` persistence/queue, без LLM в request path):

```text
requests=1000
concurrency=50
throughput_rps=731.35
failures=0
latency_p50_ms=48.57
latency_p95_ms=160.46
latency_p99_ms=279.78
under_500ms_pct=99.90
```

Это проверка порядка latency PoC, а не production capacity benchmark. Docker/PostgreSQL/Redis/Celery и GPU inference должны измеряться отдельно в целевой среде.

## Допущения и ограничения

- rule-based classifier и маленькая KB используются как baseline, а не как production ML quality claim;
- threshold `0.80` для classifier и `0.15` для retrieval требуют калибровки на исторических данных;
- PoC не реализует Kubernetes, migrations, transactional outbox, полноценный tracing и operator UI;
- автоматически не закрываются payment/refund/security и другие действия с высоким бизнес-риском;
- Qwen Docker variant требует рабочий NVIDIA container runtime и финальную проверку на целевой машине.

## Документация

- [Architecture](docs/architecture.md)
- [ML/LLM design](docs/ml.md)
- [Monitoring](docs/monitoring.md)
- [Risks and operations](docs/risks-and-ops.md)
- [AI usage](AI_USAGE.md)
- [Self review](SELF_REVIEW.md)
