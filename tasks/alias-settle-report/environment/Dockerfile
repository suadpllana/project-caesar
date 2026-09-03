FROM python:3.12-slim
WORKDIR /app
COPY app_src/bind /app/bind
COPY app_src/sets /app/sets
COPY app_src/run_bind.py /app/run_bind.py
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN python /app/run_bind.py /app/sets/barred.txt > /dev/null
