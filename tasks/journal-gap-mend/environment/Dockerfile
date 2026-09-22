# Agent image for journal-gap-mend: the recovery tool at /app with its sample journals, on the
# interpreter the brief names, and nothing that grades it.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app_src/ /app/
