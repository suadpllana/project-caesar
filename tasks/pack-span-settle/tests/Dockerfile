FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The replay stage runs as this uid, and nothing else in the container does, which is what
# lets reap.py pick its victims by owner.
RUN useradd --create-home --uid 1002 sandbox

# Every declared artifact is uploaded at its original absolute path, so those parents have to
# exist before the harness copies anything in.
RUN mkdir -p /app/pipe /app/shards /work /logs/verifier

COPY . /tests/

# The frozen answers and the sealed model are readable by root only, from build time onward.
RUN chmod +x /tests/test.sh && chmod 700 /tests/seal
