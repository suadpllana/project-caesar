FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

RUN mkdir -p /app/house /logs/verifier

COPY . /tests/

RUN set -eux; \
    pip install pytest==9.1.1 pytest-json-ctrf==0.5.2; \
    useradd --uid 1002 --no-log-init --create-home sandbox; \
    install -d -m 755 /work; \
    install -d -m 700 /say; \
    cp -a /tests/pristine /pristine; \
    chmod 0600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py; \
    chmod 0755 /tests/test.sh /tests/reap.py; \
    python -c "import json, pathlib; json.loads(pathlib.Path('/tests/gt.json').read_text())"

WORKDIR /tests
