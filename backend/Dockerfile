FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-interaction --no-ansi

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
