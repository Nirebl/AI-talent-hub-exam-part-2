# Risks and Operations

## Highload и надёжность

1. **Разделён fast/slow path.** Classification, PII и routing выполняются синхронно; retrieval/LLM generation — асинхронно. LLM latency поэтому не влияет на ориентир `≤500 ms` hot path.
2. **Burst поглощается очередью.** При 10–20k тикетов за 10 минут вход составляет примерно 17–33 req/s; API быстро persist/enqueue, а generation workers масштабируются независимо. Контролируются queue depth и oldest-task age относительно 15-минутного SLA.
3. **LLM outage деградирует в human route.** Ticket и audit не теряются; недоступность LLM не должна останавливать приём/маршрутизацию. Для worker delivery предусмотрены late ack и idempotent terminal-state checks.
4. **Durability важнее automation.** PostgreSQL — source of truth, Redis — broker. До production нужны migrations, HA, transactional outbox/DLQ и корректная обработка concurrent idempotency races.

## Privacy, safety и risk

1. **PII не отправляется в LLM path.** PoC детектирует email/phone/card-like data и переводит ticket человеку; production требует более полного detector/redaction и запрета raw PII в logs/telemetry.
2. **Высокорисковые категории не auto-close.** `payment`, `refund`, `security` и любые реальные финансовые/security actions требуют human-in-the-loop независимо от classifier confidence.
3. **Prompt injection считается untrusted input.** LLM получает grounded KB context и ограниченную инструкцию; после generation отдельный deterministic safety layer блокирует PII, unauthorized financial claims и internal prompt/routing leakage.
4. **Все решения аудируются.** `Decision` хранит route/reason/model-policy versions, `RetrievalResult` — найденные документы/rank/score/version, `Answer` — source/model/status. Это позволяет расследовать wrong automation и откатывать версии.
