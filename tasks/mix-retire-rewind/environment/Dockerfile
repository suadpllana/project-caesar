FROM python:3.12-slim

WORKDIR /app

COPY app_src/ ./

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN python run_feed.py plans/tiny.txt > /dev/null
