FROM python:3.12-slim

ENV PYTHONPATH=/tests \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The uid the scheduler run drops to. It owns a temporary directory and nothing else.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# Everything the verifier needs travels with it: the grader, the sealed model, the scenario
# generator, the recorded schedules, and an untouched copy of the tree. The agent's single
# declared file is laid over that copy at trial time, so an edit made anywhere else never runs.
COPY . /tests/

# The untouched copy is moved out of /tests, which the run may list. Left where it was, it would
# be a path the run could read the scheduler back from after overwriting the tree it executes.
RUN mv /tests/pristine /pristine

# Uploaded artifacts arrive at the absolute paths they had, so the parent has to exist already.
RUN mkdir -p /app/rt

# Recorded schedules, sealed model and grader are root only. scen.py and sched.json stay readable
# deliberately: the run has to build the same task sets the grader will, and knowing which task
# sets those are does not produce the schedules they end on.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/scen.py /tests/runner.py /tests/sweep.py /tests/sched.json
