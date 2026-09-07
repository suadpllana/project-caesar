FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app_src/ /app/

RUN set -e; for s in /app/cases/*.txt; do python /app/run_sheet.py "$s" > /dev/null; done
