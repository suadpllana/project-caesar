FROM python:3.12-slim

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 \
 && useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# Declared artifacts are uploaded to their original absolute paths, so the parent of every one of
# them has to exist before the upload happens. This stays its own instruction: a structural check
# that reads Dockerfile instructions rather than raw lines cannot see a mkdir that is hiding
# behind a line continuation, and the submission is rejected with the directory never created.
RUN mkdir -p /app/srv

# Grading is baked in, because the harness does not copy tests/ into this image at trial time.
# That means the grader, the sealed model, the enumerated jobs, the job generator, the answers to
# the enumerated jobs, and an untouched copy of the server tree.
COPY . /tests/

# The untouched copy leaves /tests so the run cannot reach it by path, and so the grader has
# something to compare the executed tree against that the run could not have written. Then the
# model, the answers and the grader become root-only. The run is welcome to read runner.py,
# cases.py and gen.py: knowing which jobs execute, and how the rest are built, produces not one of
# their traces, because the seed is made from /dev/urandom after the agent has finished. Which
# rows the grader compares would be a different matter, so it is sealed with the answers.
RUN mv /tests/pristine /pristine \
 && chmod 755 /tests \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 644 /tests/runner.py /tests/cases.py /tests/gen.py /tests/reap.py
