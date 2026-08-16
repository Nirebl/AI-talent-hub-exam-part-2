# Monitoring

## 1. Что должна доказать эксплуатация

Наблюдаемость нужна не только для uptime. Она должна показать, что система действительно решает исходную задачу: снимает операторскую нагрузку и ускоряет типовые обращения **без ухудшения CSAT, reopen и SLA**.

## 2. Технические SLI

### Hot path

- request rate и 4xx/5xx;
- `routing.total_ms` p50/p95/p99;
- classification/PII/policy/DB/enqueue latency;
- PostgreSQL availability/connection pool;
- idempotency replay/conflict rate.

Стартовый alert: `routing p95 > 500 ms` в устойчивом окне.

### Async path

- queue depth;
- oldest task age;
- enqueue/consume rate;
- worker count/availability;
- retry/unhandled-error rate;
- retrieval/LLM/safety latency.

При first response SLA 15 минут стартовый critical alert разумно поставить раньше SLA, например `oldest task age > 10 min`.

## 3. ML/RAG metrics

### Classification

- category distribution;
- confidence histogram;
- low-confidence rate;
- risky-class share;
- delayed-label macro F1 / per-class recall;
- calibration drift.

### Retrieval

- top-1 score distribution;
- insufficient-context rate;
- Recall@k/MRR на размеченной выборке;
- human rejection/edit rate по retrieved document/version.

### Generation

- LLM failure rate;
- abstention rate;
- unsafe-output rate;
- human accept/edit/reject;
- reopen/CSAT для auto-resolved tickets.

## 4. Как отличать model degradation от изменения входного потока

Смотрю одновременно на **input drift** и **outcome quality**.

Input drift signals:

- channel/language/category mix;
- text length/token distribution;
- classifier confidence distribution;
- embedding/retrieval score distribution;
- доля incident-like traffic.

Outcome signals:

- delayed-label F1/recall;
- operator correction rate;
- false-safe rate;
- reopen;
- CSAT.

Диагностика:

| Input drift | Quality | Интерпретация |
|---|---|---|
| вырос | ухудшилась | вероятен distribution shift / новый incident |
| стабилен | ухудшилась | model/KB/prompt regression или bad rollout |
| вырос | стабильна | система пока справляется, наблюдать coverage/cost |
| стабилен | стабильна | normal operation |

Для incident burst важна отдельная segment-level аналитика, иначе массовая новая тема может выглядеть как «сломавшаяся модель».

## 5. LLM cost monitoring

Контролируются:

- LLM calls/day;
- input/output tokens;
- calls per auto-resolved ticket;
- estimated ₽/1k tickets и ₽/day;
- fallback/abstention, чтобы не платить за бесполезные вызовы;
- для local GPU — utilization, generation throughput и cost per GPU-hour.

Budget alert ставится на дневную стоимость и на резкое изменение `LLM calls / incoming tickets`.

Cost guardrails в дизайне:

- risky/PII/low-confidence ticket не вызывает LLM;
- слабый retrieval останавливает generation;
- top-k и token limits ограничены;
- generation асинхронна и масштабируется отдельно.

## 6. Бизнес-метрики

Без отдельного `product.md` отслеживаются:

- automation rate;
- operator-handled tickets/day;
- first response SLA breach rate;
- CSAT, отдельно human vs automated;
- reopen rate, отдельно human vs automated;
- estimated operator minutes/₽ saved;
- cost per successfully automated ticket.

Главный online критерий успеха: **рост доли безопасно закрытых без оператора тикетов при неухудшении CSAT/reopen/SLA**.

## 7. Стартовые alerts

Critical:

```text
API 5xx > 2%
PostgreSQL unavailable
routing p95 > 500 ms
oldest generation task > 10 min
no active workers
confirmed PII leak / unauthorized financial answer
```

Warning:

```text
low-confidence rate резко вырос
insufficient-retrieval rate резко вырос
LLM fallback/cost выше baseline
queue depth растёт несколько окон подряд
automated reopen/CSAT хуже control
```

## 8. Что есть в PoC

`GET /metrics` использует простой in-memory `MetricsRecorder` и показывает stage latency/counters:

```text
routing.classification_ms
routing.pii_detection_ms
routing.policy_ms
routing.persistence_ms
routing.enqueue_ms
routing.total_ms
generation.queue_wait_ms
generation.retrieval_ms
generation.llm_ms
generation.safety_ms
generation.total_ms
routing.route.*
generation.fallback.*
```

Application зависит от metrics port, поэтому production adapter можно заменить на Prometheus/OpenTelemetry без изменения use cases.

## 9. PoC load check

Локально выполнено:

```text
1000 requests
concurrency=50
0 failures
p50=48.57 ms
p95=160.46 ms
p99=279.78 ms
99.90% <= 500 ms
```

Тест использовал memory persistence/queue и не включает Docker/PostgreSQL/Redis/GPU overhead. Это smoke/capacity sanity check hot path, а не production benchmark.
