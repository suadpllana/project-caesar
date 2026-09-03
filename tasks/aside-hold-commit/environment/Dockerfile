FROM python:3.12-slim

COPY app_src/srv /app/srv
COPY app_src/runs /app/runs
COPY app_src/run_stream.py /app/run_stream.py

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

RUN python run_stream.py runs/quote.txt > /dev/null \
 && python run_stream.py runs/tool.txt > /dev/null
