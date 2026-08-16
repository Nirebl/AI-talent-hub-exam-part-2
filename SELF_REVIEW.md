# Self Review

## Самая слабая часть

Самая слабая часть решения — **ML quality, а не backend architecture**. Текущий classifier rule-based, knowledge base маленькая, а TF-IDF retrieval threshold подобран под PoC. Это достаточно для демонстрации control flow, но не позволяет делать вывод о реальной доле безопасной автоматизации на production traffic.

Вторая слабая часть — distributed reliability: adapters для PostgreSQL/Celery есть, но production-grade transaction/outbox/retry semantics сознательно не реализованы.

## Ключевые предположения

- исторические тикеты имеют хотя бы частично пригодные operator category/route labels;
- около 40% повторяющегося трафика действительно содержит сегмент, который можно безопасно автоматизировать;
- hard-risk categories можно определить policy и не отдавать LLM;
- knowledge base является достаточно авторитетным источником ответа;
- first response важнее мгновенного auto-close, поэтому async generation допустима;
- экономия 150 ₽/ticket — это верхнеуровневая стоимость мощности оператора, а не гарантированная cash saving.

## Нерешённые риски

- concurrent duplicate requests могут столкнуться на DB unique constraint между lookup и insert;
- между DB commit и Celery enqueue нет transactional outbox;
- нет real historical dataset для calibration classifier/retrieval thresholds;
- PoC PII detector неполный;
- in-memory metrics не дают общей картины нескольких API/worker replicas;
- новый массовый incident может резко снизить retrieval coverage и заполнить human queue.

## Что я сделал бы за ещё 2 дня

### День 1

1. Собрал бы небольшой anonymized historical validation set с oversampling risky/rare categories.
2. Сравнил rules vs TF-IDF+linear classifier vs compact multilingual encoder; откалибровал confidence thresholds.
3. Добавил semantic/hybrid retrieval и измерил Recall@k/MRR против текущего TF-IDF.
4. Прогнал distributed Docker E2E/load test с PostgreSQL/Redis/Celery и fault injection LLM/Redis/worker restart.

### День 2

1. Добавил DB Unit of Work + transactional outbox и migrations.
2. Подключил Prometheus/OpenTelemetry dashboards/alerts.
3. Добавил sampled shadow evaluation и operator feedback fields.
4. Оформил canary rollout: shadow -> suggest-only -> auto-send только для safe taxonomy.

## Что нужно до production

- production classifier/retriever evaluation на реальных данных;
- data retention/redaction/privacy review;
- secrets/RBAC/network policies;
- PostgreSQL/Redis HA, backups, migrations;
- reliable publication/outbox + retry/DLQ policy;
- rate limiting и incident-mode degradation;
- observability across replicas;
- model/KB/prompt version rollout and rollback;
- human review tooling и feedback loop;
- security review prompt injection/data exfiltration scenarios.

## Что не стоит полностью автоматизировать

Я бы не разрешал LLM самостоятельно закрывать:

- payment/refund disputes;
- security incidents и identity verification;
- account actions с необратимыми последствиями;
- кейсы с PII, юридическими/финансовыми обязательствами;
- ambiguous/low-confidence tickets и новые incident clusters.

Даже после роста качества эти категории скорее подходят для operator copilot/suggest mode, а не безусловного auto-send.

## Какие данные пилота заставили бы меня остановить проект

Пилот нужно остановить или откатить auto-send, если выполняется хотя бы одно из условий:

- подтверждённый PII leak или несанкционированное финансовое/security действие — **немедленный stop**;
- materially incorrect/unsafe automation > 1% в audited sample;
- reopen для automated tickets устойчиво выше текущего baseline 9% более чем на 3 п.п. (то есть >12%) без компенсирующего эффекта;
- automated CSAT падает ниже 4.0 или статистически значимо хуже human/control;
- first-response SLA breaches растут из-за queue backlog;
- после пилота не видно существенного снижения операторской нагрузки/стоимости при соблюдении guardrails.

Иными словами, automation rate сам по себе не является критерием успеха. Если система экономит время, но ухудшает безопасность или пользовательский опыт, её нельзя масштабировать.

## Текущее состояние проверки

- local happy/risky E2E через FastAPI проверены;
- local Qwen generation проверена;
- 90 tests проходят;
- local hot-path load check: p95 160.46 ms, p99 279.78 ms, 99.90% запросов ≤500 ms;
- Docker images и API/PostgreSQL/Redis/Celery services были реально подняты; выявленная runtime-проблема с KB path исправлена через `KNOWLEDGE_BASE_PATH`;
- полный Qwen-in-Docker E2E не считаю доказанным до успешного финального ответа worker на целевой машине.

Это сознательно честная граница между тем, что уже проверено, и тем, что только реализовано как вариант deployment.
