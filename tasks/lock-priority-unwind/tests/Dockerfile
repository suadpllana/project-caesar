FROM python:3.12-slim

# The verifier carries its own copy of everything: the tests, the sealed model, the scenario
# set and generator, the recorded schedules, and an untouched copy of the tree. The agent's one
# declared file is laid over that copy at trial time, so an edit anywhere else never runs.
COPY . /tests/

RUN cp -a /tests/pristine /pristine \
    && rm -rf /tests/pristine

# Artifacts are uploaded at the absolute paths they had, so the parent has to exist.
RUN mkdir -p /app/rt

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The uid the scheduler run drops to. It owns its own temporary directory and nothing else.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# The recorded schedules, the sealed model and the grader are root only. The run reads scen.py
# and sched.json, which is fine and necessary: it has to build the same task sets the grader
# will, and knowing which task sets those are does not produce the schedules they end on.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/scen.py /tests/runner.py /tests/sweep.py /tests/sched.json

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1
