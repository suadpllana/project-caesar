FROM python:3.12-slim

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The uid the run drops to. It owns a scratch directory and nothing besides.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# Declared artifacts are re-materialized at their original absolute paths, so the
# parent of every one of them has to exist before that upload happens.
RUN mkdir -p /app/flow

# Nothing copies tests/ in at trial time, so it is baked: the grader, the sealed
# model, the plan generator, the enumerated cases, the answers, and an untouched
# copy of the machine tree.
COPY . /tests/

# The untouched copy leaves /tests, so the run cannot reach it by path and the
# grader has something to compare the executed tree against that the run could
# never have written.
RUN mv /tests/pristine /pristine

# Root alone reads the model, the answers and the grader. runner.py, gen.py and
# cases.py stay readable: which plans execute, and how the rest are shaped,
# produces none of their traces, because the seed is drawn once the agent has
# stopped. Which rows the grader compares would be another matter, so
# test_outputs.py is sealed with the answers.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/tests
