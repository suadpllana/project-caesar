FROM python:3.12-slim
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY app_src /app
RUN find /app -type d -exec chmod 0755 {} + && find /app -type f -exec chmod 0644 {} +
WORKDIR /app
