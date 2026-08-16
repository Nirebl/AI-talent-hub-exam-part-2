FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY src ./src
COPY data ./data

RUN pip install --upgrade pip     && pip install -r requirements.txt     && pip install --no-deps .

CMD ["python", "-m", "uvicorn", "support_ai.infrastructure.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
