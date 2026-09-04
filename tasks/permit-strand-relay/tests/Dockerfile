FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/tests
ENV PYTHONHASHSEED=0

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2
RUN useradd --uid 1002 --no-create-home --shell /usr/sbin/nologin sandbox

COPY . /tests/
WORKDIR /tests

RUN mkdir -p /app/pol
RUN mkdir -p /work
RUN install -d -m 700 /logs/verifier

RUN mv /tests/pristine /pristine
RUN chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
RUN chmod 755 /tests/test.sh
