FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen

COPY . .

RUN mkdir -p /app/data

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "-m", "app.main"]

