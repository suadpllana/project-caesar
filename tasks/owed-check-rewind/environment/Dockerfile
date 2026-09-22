FROM python:3.12-slim

# The executor and its programs need nothing beyond the standard library.
WORKDIR /app
COPY app_src/ ./

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
