FROM python:3.12-slim

# An unprivileged account for the run: it owns one scratch directory and nothing
# else, and it is the uid reap.py sweeps once the run is over.
RUN useradd -u 1002 -m -s /usr/sbin/nologin runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/tests

# Everything the verifier needs arrives at build time. test.sh reaches no network.
RUN pip install --no-cache-dir "pytest==9.1.1" "pytest-json-ctrf==0.5.2"

# Separate mode does not upload tests/, so they are baked in: the grader, the
# sealed model, the trace generator, the enumerated traces, the answers, and an
# untouched copy of the engine tree.
COPY . /tests/

# The untouched copy leaves /tests. No path reachable from inside the run leads
# to it, and the grader gains a tree to hold the executed one against.
RUN mv /tests/pristine /pristine

# Artifacts come back at the absolute paths they had, so their parents have to
# exist before the platform puts them there.
RUN mkdir -p /app
RUN mkdir -p /app/eng

# Root alone reads the model, the answers and the grader. Which traces run gives
# nothing away, because the nonce shaping the other three hundred is drawn after
# the agent stops; which lines the grader compares would be another matter.
RUN chmod 755 /tests
RUN chmod 600 /tests/oracle.py /tests/gt.json /tests/test_outputs.py
RUN chmod 644 /tests/cases.py /tests/gen.py /tests/reap.py /tests/runner.py
