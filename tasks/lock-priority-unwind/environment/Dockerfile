FROM python:3.12-slim

WORKDIR /app

COPY app_src/rt/ /app/rt/
COPY app_src/conf/ /app/conf/
COPY app_src/cases/ /app/cases/
COPY app_src/run_sched.py /app/run_sched.py

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN python -c "from rt import boot, core, lock, prio, task" \
    && python run_sched.py cases/inversion.json > /dev/null \
    && python run_sched.py cases/handover.json > /dev/null
