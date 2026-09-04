FROM python:3.12-slim

COPY . /tests/
WORKDIR /tests

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/tests

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 \
 && mv /tests/pristine /pristine \
 && mkdir -p /app/note /app/scr /app/rev /work \
 && install -d -m 700 /logs/verifier \
 && useradd --uid 1002 --no-create-home --shell /usr/sbin/nologin sandbox \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 755 /tests/test.sh
