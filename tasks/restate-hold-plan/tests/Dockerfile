FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --uid 1002 --no-create-home --shell /usr/sbin/nologin planner

RUN mkdir -p /app
RUN mkdir -p /app/plan
RUN mkdir -p /logs/verifier
RUN mkdir -p /work

COPY . /tests/

RUN chmod 700 /tests/seal
RUN chmod 755 /tests/test.sh
