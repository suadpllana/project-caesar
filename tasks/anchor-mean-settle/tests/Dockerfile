FROM python:3.12-slim

# Everything the verifier needs is baked in here: nothing at trial time may touch the network.
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

ENV PYTHONDONTWRITEBYTECODE=1

# The uid stage one drops to. Nothing else in this image runs as it, which is what makes a
# surviving process identifiable by owner.
RUN useradd --create-home --uid 1002 sandbox

# Each declared artifact needs its parent to exist before the platform uploads it.
RUN mkdir -p /app
RUN mkdir -p /app/pan
RUN mkdir -p /work
RUN mkdir -p /logs/verifier

COPY . /tests/

RUN chmod +x /tests/test.sh
RUN chmod 700 /tests/seal
