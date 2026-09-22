FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 \
 && useradd --create-home --uid 1002 --shell /usr/sbin/nologin sandbox

RUN mkdir -p /app/rs /logs/verifier /work

COPY . /tests/

RUN chmod 700 /tests/seal && chmod 755 /tests/test.sh \
 && test -f /tests/seal/model.py && test -f /tests/seal/gt.json \
 && test -f /tests/pristine/run_ask.py && test -d /tests/pristine/rs
