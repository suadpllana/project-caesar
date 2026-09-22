FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2
RUN useradd --uid 1002 --create-home sandbox

RUN mkdir -p /app/fe
RUN mkdir -p /logs/verifier
RUN mkdir -p /work
RUN mkdir -p /exam

COPY . /tests/
RUN chmod 700 /tests/seal && chmod +x /tests/test.sh
