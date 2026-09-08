FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --create-home --uid 1002 sandbox \
    && mkdir -p /app /app/train /work /logs/verifier

COPY . /tests/

RUN chmod +x /tests/test.sh \
    && chown -R root:root /tests/seal \
    && chmod 700 /tests/seal \
    && chmod 600 /tests/seal/*
