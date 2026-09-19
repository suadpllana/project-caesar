FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

COPY . /tests/

RUN mkdir -p /app/feed

RUN mkdir -p /work

RUN mkdir -p /logs/verifier

RUN useradd --create-home --uid 1002 sandbox && chmod +x /tests/test.sh && chmod 700 /tests/seal
