FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN mkdir -p /app/pol
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=0

COPY . /tests/

RUN useradd --uid 1002 --no-create-home --shell /usr/sbin/nologin sandbox
RUN mv /tests/pristine /pristine

RUN chmod 0700 /logs/verifier
RUN chmod 0600 /tests/gt.json
RUN chmod 0600 /tests/oracle.py
RUN chmod 0600 /tests/test_outputs.py
RUN chmod 0755 /tests/test.sh

WORKDIR /tests
