# AI Usage

Во время выполнения задания я использовал ChatGPT как coding copilot и дополнительный инструмент для ускорения разработки в условиях ограниченного времени. Существенную часть кода я писал и дорабатывал самостоятельно: проектирование архитектуры, domain/application logic, routing policy, интеграцию компонентов, debugging и E2E-проверку.

AI не использовался как полностью автономный генератор проекта. Работа шла итеративно: я определял следующий технический шаг, писал или правил код, запускал систему и тесты, после чего использовал AI для ускорения отдельных реализационных задач и дополнительного review.

## Что я реализовывал и определял самостоятельно

Я сформировал основную архитектуру решения и ключевые технические решения:

- FastAPI как synchronous entrypoint;
- разделение domain, application, adapters и infrastructure;
- разделение `Prediction`, `Decision` и `Answer`;
- deterministic RiskPolicy вместо LLM-based routing;
- human fallback для risky, PII и low-confidence обращений;
- asynchronous generation вне hot path;
- retrieval перед LLM;
- safety validation перед отправкой ответа;
- audit trail для routing и retrieval;
- idempotency по `(channel, external_id)`;
- Redis/Celery как distributed queue;
- PostgreSQL как shared persistence;
- отдельный Qwen worker;
- readiness, runtime metrics и load testing.

Я также самостоятельно писал и редактировал значительную часть прикладного кода, в том числе use cases, domain rules, API flow, интеграцию retrieval/LLM/safety и обработку fallback-сценариев.

Во время разработки я вручную проверял систему через FastAPI `/docs`, тесты и Docker logs и исправлял поведение, когда реальный runtime расходился с ожидаемой архитектурой.

## Где AI использовался наиболее активно

### Boilerplate и заменяемые adapters

AI в основном ускорял однотипный код:

- Pydantic schemas;
- repository interfaces;
- in-memory repositories;
- mock/fake implementations;
- часть SQLAlchemy mappings;
- фабрики зависимостей;
- Celery/Docker configuration drafts;
- тестовые fixtures.

Это позволило не тратить основное время экзамена на механический boilerplate.

### Tests

AI помогал предлагать дополнительные test cases и быстро оформлять часть тестового кода:

- low-confidence routing;
- risky categories;
- PII;
- unavailable LLM;
- unsafe generated output;
- duplicate requests;
- repeated worker delivery;
- retrieval threshold.

Сами сценарии я проверял запуском test suite и ручным E2E.

### Documentation

Markdown-документация проекта в значительной степени создавалась с помощью AI на основе уже реализованного решения.

После генерации я самостоятельно:

- проверял документацию на соответствие фактическому коду и runtime-поведению;
- исправлял неточности и формулировки;
- дополнял отсутствующие детали;
- удалял утверждения, которые не подтверждались реализацией;
- приводил структуру и описание компонентов в соответствие с итоговой архитектурой.

Таким образом, AI использовался здесь прежде всего как инструмент для ускорения оформления и структурирования документации, а не как источник технической истины.

## ML/LLM decisions

Я сознательно разделил три разные задачи:

```text
classification -> что за тикет
risk policy    -> можно ли автоматизировать
generation     -> как сформулировать ответ
```

LLM не используется как универсальный classifier или risk engine.

Для classification в PoC используется deterministic baseline, так как в задании нет готового размеченного production dataset.

Для retrieval используется TF-IDF baseline. Его задача в PoC — показать retrieval contract, confidence threshold и auditability.

Qwen подключён только как answer generator поверх найденного контекста. Он не принимает финансовые, security или routing decisions.

## Что я сознательно не стал делать

Я отказался от частей, которые увеличивали бы объём, но почти не улучшали доказательство решения в рамках 4-часового PoC:

- Kubernetes;
- feature store;
- отдельный vector database;
- полноценный ML training pipeline;
- production migration stack;
- distributed tracing backend;
- transactional outbox;
- отдельный inference service.

Приоритетом были рабочий E2E, безопасный fallback и прозрачность решений системы.

## Ошибки AI и ручная проверка

AI-предложения не принимались без проверки.

Во время реализации были обнаружены и исправлены, например:

- слишком общий сигнал в rule-based classifier;
- пропущенные зависимости при расширении retrieval audit;
- конфликт `requirements-llm.txt` с `.dockerignore`;
- неправильное вычисление пути к knowledge base внутри Docker;
- несоответствия между локальным in-memory execution и distributed API/worker execution.

Такие ошибки обнаруживались через tests, Docker startup logs и ручные API-запросы.

## Итоговый подход

AI использовался как ускоритель разработки, а не как автономный исполнитель задания.

Архитектура, значимая часть реализации, интеграция компонентов, debugging, тестирование и финальная проверка результата выполнялись мной. Документация в основном генерировалась с помощью AI, но затем вручную проверялась, редактировалась и приводилась мной в соответствие с фактической реализацией.

Я не рассматривал ответы AI как источник истины: любое существенное изменение должно было либо пройти automated tests, либо быть подтверждено ручным E2E/runtime check.
