FROM python:3.12-slim

WORKDIR /app

# Install Poetry and project dependencies
RUN pip install --no-cache-dir poetry

COPY pyproject.toml /app/pyproject.toml
RUN poetry config virtualenvs.create false \
  && poetry install --only main --no-interaction --no-ansi

COPY app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

