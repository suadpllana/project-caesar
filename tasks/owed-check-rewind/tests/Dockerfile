FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# The grader's only dependencies; the executor under test needs the standard library alone.
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# Stage one runs submitted code as this user and never as root.
RUN useradd --create-home --uid 2201 runner

# One directory per line: the six collected files land in /app/tx, and the verdict and the
# stage-one record live apart from it.
RUN mkdir -p /app
RUN mkdir -p /app/tx
RUN mkdir -p /logs/verifier
RUN mkdir -p /scratch

COPY . /tests/
RUN chmod 700 /tests/seal && chmod 755 /tests/test.sh
