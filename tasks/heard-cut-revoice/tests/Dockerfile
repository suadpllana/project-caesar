FROM python:3.12-slim

RUN mkdir -p /app/sr /work /logs/verifier

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 \
 && groupadd --gid 1002 reader \
 && useradd --uid 1002 --gid 1002 --no-create-home --shell /usr/sbin/nologin reader

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY . /tests/
RUN chmod 755 /tests/test.sh && chmod 700 /tests/seal
