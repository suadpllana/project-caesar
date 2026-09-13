FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --create-home --uid 1002 sandbox

RUN mkdir -p /app
RUN mkdir -p /app/cfg
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

COPY . /tests/

RUN chown -R root:root /tests \
    && find /tests -type d -exec chmod 755 {} + \
    && find /tests -type f -exec chmod 644 {} + \
    && chmod 755 /tests/test.sh \
    && chmod 700 /tests/seal
