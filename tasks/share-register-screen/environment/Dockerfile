FROM python:3.12-slim
WORKDIR /app
COPY app_src .
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
RUN python -c "import reg.run, pol.screen"
