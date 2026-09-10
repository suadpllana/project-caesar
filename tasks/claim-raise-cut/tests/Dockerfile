FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --create-home --uid 1002 sandbox

RUN mkdir -p /app
RUN mkdir -p /app/hold
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

COPY . /tests/

RUN chmod +x /tests/test.sh && chmod 700 /tests/seal
