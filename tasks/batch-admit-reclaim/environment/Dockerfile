FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app_src/eng /app/eng
COPY app_src/traces /app/traces
COPY app_src/run_serve.py /app/run_serve.py
RUN python /app/run_serve.py /app/traces/steady.txt > /dev/null
