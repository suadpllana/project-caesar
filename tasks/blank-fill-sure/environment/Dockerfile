FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app_src/ /app/

RUN test -f /app/run_ask.py && test -d /app/rs && test -f /app/progs/tiny.txt
