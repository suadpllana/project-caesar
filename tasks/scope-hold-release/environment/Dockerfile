FROM python:3.12-slim
COPY app_src /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN python run_wire.py cases/plain.txt > /dev/null
RUN python run_wire.py cases/wide.txt > /dev/null
