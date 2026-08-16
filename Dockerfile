FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-llm.txt pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY src ./src
COPY data ./data

RUN pip install --no-deps .

FROM base AS qwen-worker

RUN pip install -r requirements-llm.txt

CMD ["celery", "-A", "support_ai.infrastructure.celery_app:celery_app", "worker", "--loglevel=INFO", "--queues=response_generation", "--concurrency=1"]

FROM base AS runtime

CMD ["python", "-m", "uvicorn", "support_ai.infrastructure.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
