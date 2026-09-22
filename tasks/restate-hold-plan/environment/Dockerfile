FROM python:3.12-slim

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY app_src/ /app/
WORKDIR /app

CMD ["python3", "run_plan.py", "pipes/small.txt"]
