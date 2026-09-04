FROM python:3.12-slim

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY app_src/lnk /app/lnk
COPY app_src/pol /app/pol
COPY app_src/cases /app/cases
COPY app_src/relay.py /app/relay.py

WORKDIR /app

RUN set -eux; \
    python relay.py cases/handover.json > /dev/null; \
    python relay.py cases/lull.json > /dev/null
