# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts

RUN pip install --no-cache-dir -e ".[dev,sim]"

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["nestweaver"]
CMD ["doctor"]
