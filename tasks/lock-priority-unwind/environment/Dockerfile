FROM python:3.12-slim
WORKDIR /app
ADD app_src/ ./
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN set -e; python run_sched.py cases/handover.json >/dev/null; python run_sched.py cases/inversion.json >/dev/null
