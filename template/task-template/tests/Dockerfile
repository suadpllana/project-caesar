FROM python:3.12-slim

# Verifier image. REQUIRED: in separate-verifier mode the harness does NOT copy tests/
# into the container for you — this image must own /tests itself. Without this file the
# trial fails with "has no environment definition" before any test runs.
#
# The build context is this tests/ directory, so the COPY below bakes in test.sh,
# test_outputs.py, and any ground truth files kept here. Ground truth belongs here and
# only here — never in environment/.
COPY . /tests/

# Create the parent directory of every path declared in `artifacts` in task.toml.
# The harness uploads the agent's artifacts into this container at their original
# absolute paths, and verification fails with "Could not find the file ... in container"
# if the parent directory does not exist. Adjust to match your artifact paths.
RUN mkdir -p /app

# The verifier must be SELF-CONTAINED: every tool and dependency verification needs is
# installed HERE, at build time, where the fetch is pinned and sealed. test.sh must never
# touch the network — no curl | sh, no pip install, no apt-get at trial time; the platform
# rejects both as blocking errors. The pytest pins below are the canonical ones.
RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# How the verifier sees the agent's work: every path declared in `artifacts` in task.toml
# is re-materialized at its ORIGINAL absolute path. If the agent wrote /app/output.json,
# the tests read /app/output.json. Nothing else from the agent's container exists here.
#
# Pin every Python package with ==; never pin apt packages; never use FROM --platform=.
