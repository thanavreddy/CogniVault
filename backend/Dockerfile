FROM python:3.11-slim

WORKDIR /app/backend

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

COPY backend/ ./

RUN mkdir -p /app/backend/data/documents

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]