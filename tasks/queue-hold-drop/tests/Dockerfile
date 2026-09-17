FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

# Everything the verifier needs, pinned and sealed at build time. Nothing here reaches the
# network again once the image exists, and tests/test.sh installs nothing.
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The uid that runs the submitted service. Nothing else in this container runs as it, which is
# what lets tests/reap.py recognise a survivor by ownership.
RUN useradd --create-home --uid 1002 sandbox

# The parent of every collected artifact, and the two directories the two stages use.
RUN mkdir -p /app
RUN mkdir -p /app/pend
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

COPY . /tests/

# The sealed side goes out of the sandbox uid's reach before anything it wrote can run.
RUN chmod +x /tests/test.sh && chmod 700 /tests/seal
