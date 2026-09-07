FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The uid the run drops to. It owns its scratch directory and nothing else, and it is
# created before anything is copied so the layer is cached across test edits.
RUN useradd --uid 1002 --create-home --shell /usr/sbin/nologin sandbox

# In separate mode the harness does not upload tests/, so everything the verifier needs is
# baked in here: the grader, the sealed model, the session generators, the enumerated
# cases, the ground truth, and an untouched copy of the engine tree.
COPY . /tests/

# The untouched copy moves out of /tests, so the run cannot reach it by path and the
# grader has something to compare the executed tree against that the run could not write.
RUN mv /tests/pristine /pristine

# Declared artifacts are re-materialized at their original absolute paths, so the parent
# of every one of them has to exist before that upload happens.
RUN mkdir -p /app/eng

# What the run may read: runner.py, gen.py, cases.py and reap.py. Knowing which sessions
# execute, and how the rest are built, produces none of their events, because the seed is
# made from /dev/urandom after the agent has finished. Which rows the grader compares
# would be a different matter, so test_outputs.py is sealed next to the answers.
RUN chmod 0755 /tests \
    && chmod 0600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 0644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1
