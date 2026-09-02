FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --uid 1002 --create-home sandbox \
 && mkdir -p /app/core /work /rep /logs/verifier

COPY . /tests/

RUN cp -a /tests/pristine /pristine \
 && chmod 700 /rep \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 755 /tests/test.sh /tests/reap.py

WORKDIR /tests
