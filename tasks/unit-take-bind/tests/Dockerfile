FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

# procps and util-linux give the verifier `pkill` and `setpriv`: the worker that runs
# submitted code is started under an unprivileged uid and its survivors are swept by owner.
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The uid submitted code runs as. It owns /work and nothing else.
RUN useradd --create-home --uid 1002 sandbox

# Artifact parents: the harness materialises /app/res/*.py at their original paths, and
# verification fails outright if the directory is not already there. /work is the sandbox's
# scratch, /logs/verifier the reward channel test.sh locks before anything else happens.
RUN mkdir -p /app/res /work /logs/verifier

COPY . /tests/

RUN chmod 755 /tests/test.sh
