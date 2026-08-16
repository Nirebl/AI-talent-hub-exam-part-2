# ML and LLM Design

## 1. Разделение задач

В системе намеренно разделены три независимые задачи:

```text
Prediction: что это за тикет?
Decision: можно ли его автоматизировать?
Generation: как сформулировать ответ?
```

LLM используется только в третьем пункте. Risk и routing остаются deterministic.

## 2. Что решается правилами

Правила подходят там, где ошибка дороже потери automation coverage:

- запрет auto-close для `payment`, `refund`, `security`;
- PII guard;
- confidence threshold;
- output safety checks;
- idempotency и fallback reasons.

Эти правила должны быть auditable и быстро меняться без retraining.

## 3. Classification

### PoC baseline

Текущий classifier — deterministic multilingual rule-based baseline с категориями:

- `account`
- `payment`
- `refund`
- `technical`
- `security`
- `faq`
- `other`

Он возвращает category и confidence и нужен для проверки contracts/routing, а не для заявления production ML quality.

### Первый learned baseline

Для production первым обученным baseline я бы сравнил:

1. TF-IDF + logistic regression / linear SVM;
2. compact multilingual encoder classifier.

Причины: inference дешёвый, p95 предсказуемый, легко сделать calibrated confidence и сравнить с rules baseline.

### Данные

Источники:

- исторические tickets;
- текущие operator tags/routes;
- причины escalation;
- reopen/CSAT outcome;
- incident periods отдельно от обычного трафика.

Существующие operator labels можно использовать как weak labels, но перед обучением нужна проверка качества taxonomy и sample-based relabeling.

### Разметка

Минимальный процесс:

1. очистить/зафиксировать taxonomy;
2. взять stratified sample по категориям, каналам и incident traffic;
3. oversample risky и rare categories;
4. двойная разметка спорных примеров;
5. disagreements отправлять domain expert/support lead;
6. отдельно собирать low-confidence/production errors для active learning.

## 4. Low confidence

Classifier threshold в PoC: `0.80`.

Он не считается оптимальным. В production threshold выбирается на validation set по trade-off:

```text
automation coverage
vs
false-safe / incorrect automation
```

Для risky classes recall важнее общей accuracy. High confidence не может переопределить hard risk policy.

## 5. Retrieval

### PoC

Используется:

```text
TF-IDF
1–2 grams
cosine similarity
top-k = 3
```

Retrieval threshold: `0.15` для маленькой PoC KB.

При слабом top-1:

```text
route -> human
reason -> insufficient_retrieval_context
```

### Target

Для реального сервиса разумный следующий шаг:

- multilingual sentence embeddings;
- vector index, например pgvector/аналог;
- optional lexical + semantic hybrid search;
- filtering по product/version/locale;
- versioned KB.

Embeddings уместны здесь, потому что пользователи формулируют одну проблему разными словами, а точное совпадение токенов TF-IDF не всегда достаточно.

### Retrieval evaluation

- Recall@k;
- MRR;
- top-1 relevance;
- coverage above threshold;
- incorrect-context rate.

Каждый retrieval run сохраняется в audit trail, поэтому wrong answer можно связать с конкретным найденным контекстом.

## 6. LLM

### Где нужен

LLM нужен для:

- grounded response drafting;
- переформулирования KB-инструкции в понятный ответ;
- потенциально — summarization для оператора.

### Где не нужен

LLM не должен:

- определять risk policy;
- разрешать refund/compensation;
- выполнять security/account actions;
- решать, можно ли отправлять PII;
- быть единственным классификатором hot path.

### Модели и происхождение

В PoC есть:

- deterministic mock generator для тестов;
- local Qwen adapter, загружающий публичную open-weight модель по configurable model id;
- learned classifier в PoC не обучается: target-вариант должен обучаться внутри на anonymized historical support tickets и operator labels.

Публичная LLM не считается автоматически подходящей для production: до rollout нужны safety/groundedness/latency/cost evaluation на доменной выборке. Внутренние ticket data не должны попадать в публичные training pipelines; для внешнего inference нужен privacy review/redaction.

Модель вызывается только после retrieval. Prompt требует отвечать по KB context и возвращать `NEED_HUMAN_REVIEW`, если контекста недостаточно или он противоречив.

## 7. Generation safety

После LLM работает независимый deterministic checker. Он блокирует:

- empty/abstained answer;
- PII-like output;
- unauthorized financial claims;
- internal prompt/routing leakage;
- слишком длинный output.

Unsafe answer не auto-sent: он сохраняется как `rejected`, а ticket escalates to human.

## 8. Offline validation

### Classifier

- macro F1;
- per-class precision/recall;
- risky-class recall;
- confusion matrix;
- calibration / ECE;
- latency p95/p99.

### Routing

- automation rate;
- false-safe rate;
- human escalation rate;
- incorrect automation rate.

### Retrieval

- Recall@k;
- MRR;
- relevance/coverage by category and language.

### Generation

- groundedness against KB;
- hallucination/policy-violation rate;
- correct abstention;
- human acceptance/edit rate.

## 9. Online validation and feedback loop

Production labels приходят с задержкой, поэтому online quality строится из:

- operator accept/edit/reject;
- reopen;
- CSAT;
- escalation reason;
- sampled manual review автоматических ответов.

```text
production feedback
      |
      v
labeled error set
      |
      v
offline classifier/retrieval/generation evaluation
      |
      v
new version -> shadow -> canary
```

Model, policy и retriever versions сохраняются в audit records, поэтому regression можно связывать с конкретным rollout.
