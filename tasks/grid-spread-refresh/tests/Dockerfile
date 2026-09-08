FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tests

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The uid the run drops to, so the process that executes submitted code owns nothing the
# verdict is read from.
RUN useradd -u 1004 -m -s /usr/sbin/nologin rerun

# The harness uploads each declared artifact to its original absolute path, and the parent
# has to exist before it does. Kept as their own instructions: the structural gate reads
# these lines and does not follow a && chain.
RUN mkdir -p /app
RUN mkdir -p /app/sheet

# In separate mode nothing under tests/ is copied at trial time, so the grader, the sealed
# model, the case set, the generators, the hand derivations and an untouched copy of the
# runtime all have to be baked in here.
COPY . /tests/

# The untouched copy leaves /tests, so a run cannot reach it by guessing a path.
RUN mv /tests/pristine /pristine

# Only root reads the hand derivations, the model and the grader. The run may read the
# runner, the case set and the generators, none of which yields an expected report.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/sweepup.py
