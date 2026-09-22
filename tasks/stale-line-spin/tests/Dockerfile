FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN groupadd --gid 1002 runner \
 && useradd --uid 1002 --gid 1002 --create-home --shell /usr/sbin/nologin runner \
 && python3 -m pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2
RUN mkdir -p /app/sim /logs/verifier /work

COPY . /tests/
RUN chmod 0700 /tests/seal && chmod 0755 /tests/test.sh
