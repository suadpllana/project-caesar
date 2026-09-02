FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY app_src/run_ops.py /app/run_ops.py
COPY app_src/core/ /app/core/
COPY app_src/streams/ /app/streams/
