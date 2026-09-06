FROM python:3.12-slim

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/hst /app/cases
WORKDIR /app

COPY app_src/run_host.py /app/run_host.py
COPY app_src/hst /app/hst
COPY app_src/cases /app/cases

RUN python /app/run_host.py /app/cases/boot.txt /app/cases/chain.txt > /dev/null
