# Verifier image for journal-gap-mend. The five collected files are uploaded into /app/jl,
# laid over the pristine tree under /tests, and run as the unprivileged uid 1002; the grader
# itself needs pytest and its CTRF report, nothing more.
FROM python:3.12-slim

RUN mkdir -p /app/jl /logs/verifier /work
RUN useradd --uid 1002 --create-home --shell /bin/sh sandbox
RUN python3 -m pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY . /tests/
RUN chmod 0700 /tests/seal && chmod 0755 /tests/test.sh
