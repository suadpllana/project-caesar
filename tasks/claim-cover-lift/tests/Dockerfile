FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

# The unprivileged uid that runs the submitted service. Nothing else in this image uses it, so
# a live process holding it after the call has returned is a survivor.
RUN useradd --no-create-home --uid 1002 sandbox

# Artifact parents. The platform uploads the collected files at their original absolute paths.
RUN mkdir -p /app
RUN mkdir -p /app/hb
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

COPY . /tests/

RUN chmod 700 /tests/seal && chmod +x /tests/test.sh
