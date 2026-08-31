FROM python:3.12-slim

# Everything the verifier needs is baked here, because the harness does not copy tests/
# into this container at trial time: the grader, the sealed model, the program generator,
# the enumerated cases, the ground truth, and an untouched copy of the runtime tree.
COPY . /tests/

# The pristine tree moves out of /tests so the run can never reach it by path, and so the
# grader can compare the executed tree against something the run could not have written.
RUN mv /tests/pristine /pristine

# The harness re-materializes the declared artifacts at their original absolute paths, so
# the parent directory of every one of them has to exist before the upload happens.
RUN mkdir -p /app/kern

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The uid the run drops to. It owns its scratch directory and nothing else.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# The sealed model, the ground truth and the grader are readable by root only. The run is
# welcome to read runner.py, gen.py and cases.py: knowing which programs execute, and how
# the rest are built, does not produce a single one of their traces, because the seed is
# made from /dev/urandom after the agent has finished. Knowing which rows the grader
# compares would be a different matter, so test_outputs.py is sealed alongside the answers.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1
