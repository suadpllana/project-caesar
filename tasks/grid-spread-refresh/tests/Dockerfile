FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tests

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 \
    && useradd -u 1004 -m -s /usr/sbin/nologin rerun \
    && mkdir -p /app/sheet

# In separate mode the harness uploads nothing but the declared artifacts, so the grader,
# the sealed model, the case set, the generators, the hand derivations and an untouched
# copy of the runtime all have to be baked in here.
COPY . /tests/

# The untouched copy leaves /tests, so a run cannot reach it by guessing a path. The three
# files that would answer the graded question outright stay root-only; the runner, the case
# set and the generators are readable, and none of them yields an expected report.
RUN mv /tests/pristine /pristine \
    && chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/sweepup.py
