FROM python:3.12-slim

# The harness does not copy tests/ into this container at trial time, so everything the
# verifier needs is baked here: the grader, the sealed model, the journal generator, the
# enumerated cases, the ground truth, and an untouched copy of the kernel tree.
COPY . /tests/

# The untouched copy moves out of /tests, so the run cannot reach it by path and so the
# grader has something to compare the executed tree against that the run could not write.
RUN mv /tests/pristine /pristine

# Declared artifacts are re-materialized at their original absolute paths, and the upload
# fails outright if the parent directory is not already there.
RUN mkdir -p /app/pol

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The uid the run drops to. It owns its scratch directory and nothing else.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# The model, the ground truth and the grader are root-only. runner.py, gen.py and cases.py
# stay readable: the run is welcome to know which journals execute and how the rest are
# built, because the nonce is made from /dev/urandom after the agent has stopped and none
# of those files contains an answer. Which rows the grader compares would be a different
# matter, so test_outputs.py is sealed alongside the answers.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py

ENV PYTHONPATH=/tests \
    PYTHONDONTWRITEBYTECODE=1
