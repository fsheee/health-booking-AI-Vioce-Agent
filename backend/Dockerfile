FROM python:3.12-slim

RUN apt-get update -qq && apt-get install -y -qq curl > /dev/null 2>&1 && rm -rf /var/lib/apt/lists/*

RUN pip install uv --quiet

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
