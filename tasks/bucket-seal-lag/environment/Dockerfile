FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY app_src /app
WORKDIR /app
RUN python run_flow.py plans/direct.txt > /dev/null && python run_flow.py plans/redrive.txt > /dev/null
