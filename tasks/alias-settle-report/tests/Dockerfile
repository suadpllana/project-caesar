FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/tests

# Everything the verifier needs is installed here. test.sh reaches no network.
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# An unprivileged account for the run. It owns a scratch directory, nothing more.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# Nothing copies the tests in at trial time, so they are baked: the grader, the
# sealed model, the set generator, the enumerated sets, the answers, and an
# untouched copy of the machine tree.
COPY . /tests/

# That untouched copy leaves /tests. No path from inside the run reaches it, and
# the grader gains something to hold the executed tree against that the run could
# never have written.
RUN mv /tests/pristine /pristine

# Uploaded artifacts come back at the absolute paths they had, so the parent of
# each one has to exist before the platform puts them there.
RUN mkdir -p /app/bind

# Root alone reads the model, the answers and the grader. Which sets run, and how
# the rest are shaped, gives away none of their rows, because the seed is drawn
# once the agent has stopped; which rows the grader compares would be another
# matter, so test_outputs.py is sealed alongside the answers.
RUN chmod 755 /tests \
 && chmod 600 /tests/oracle.py /tests/gt.json /tests/test_outputs.py \
 && chmod 644 /tests/cases.py /tests/gen.py /tests/reap.py /tests/runner.py
