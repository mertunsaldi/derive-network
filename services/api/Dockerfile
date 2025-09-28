FROM python:3.11-slim

ENV POETRY_VERSION=1.7.1
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/* \
    && pip install "poetry==${POETRY_VERSION}"

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY services ./services
COPY schemas ./schemas
COPY examples ./examples

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

EXPOSE 8000
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
