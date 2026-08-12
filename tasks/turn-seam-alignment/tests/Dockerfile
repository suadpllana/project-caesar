FROM python:3.12-slim

# The verifier owns its own copy of everything it needs: the tests, the sealed replay,
# the merge table it encodes with, the scenario set, the ground truth, and a pristine
# copy of the loop. The agent's declared files are overlaid onto that pristine copy at
# trial time, so edits outside the declared set never reach the run.
COPY . /tests/

RUN cp -a /tests/pristine /pristine \
    && rm -rf /tests/pristine

# Two directories, because the loop run and the grading are two different trust levels.
#
# /driver is what the unprivileged run gets: the driver and the scenario set, and nothing
# else. Knowing which op sequences execute does not produce the token streams they expect,
# which is why the scenario set is allowed to be over here.
#
# /tests is everything that knows an answer, and the run cannot open any of it. That is
# not only gt.json: tests/oracle.py recomputes the same ground truth from scratch, so a
# run that could import it would not need to read the file. An earlier build left /tests
# world-readable and on the run's import path, and a probe walked straight through -
# oracle.replay() for the sequences, spans, trace and forwards, oracle.encode() to search
# each render for its cheapest legal resume, and the graded attributes written over on the
# way out, with no resume logic in the submission at all.
RUN mkdir -p /driver \
    && cp /tests/runner.py /tests/scen.py /driver/ \
    && rm /tests/runner.py

# The harness uploads the declared artifacts at their original absolute paths.
RUN mkdir -p /app/tok /app/loop

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The unprivileged uid the loop run drops to. It can write its work directory and
# nothing else that matters.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# /tests is root-only, directory included, so nothing under it can be opened, imported or
# listed by the run. /driver is what the run reads instead.
RUN chmod 700 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/audit.py \
                /tests/test_outputs.py /tests/scen.py /tests/reap.py \
                /tests/merges.json /tests/loop.json \
    && chmod 755 /driver \
    && chmod 644 /driver/runner.py /driver/scen.py

# No PYTHONPATH here: the run and the grader need different ones, and the one the grader
# needs is the one the run must not have. test.sh sets each of them per invocation.
ENV PYTHONDONTWRITEBYTECODE=1
