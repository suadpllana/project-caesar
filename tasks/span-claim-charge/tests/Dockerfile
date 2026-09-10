FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --create-home --uid 1002 sandbox

RUN mkdir -p /work
RUN mkdir -p /logs/verifier
RUN mkdir -p /app
RUN mkdir -p /app/store

COPY . /tests/

RUN chmod 700 /tests/seal && chmod +x /tests/test.sh
