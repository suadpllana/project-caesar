FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tests

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The unprivileged uid the run drops to. It gets a scratch directory and no
# other writable path anywhere.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# Declared artifacts land back at the absolute paths they had, so the parent of
# every one of them has to exist before the platform uploads them.
RUN mkdir -p /app/bay

# The harness copies nothing into this image, so the grader, the second reading,
# the feed generator, the named feeds, the answers and an untouched copy of the
# fabric are all baked here.
COPY . /tests/

# The untouched copy leaves /tests entirely. The run cannot reach it by any path,
# which is what lets the grader derive a baseline the run had no chance to write.
RUN mv /tests/pristine /pristine

# Root alone opens the answers, the second reading and the grader. runner.py,
# gen.py and cases.py stay readable: which feeds run, and how the rest are
# shaped, produces none of their rows, because the nonce is drawn after the agent
# has stopped. Which rows the grader compares would be a different matter.
RUN chmod 755 /tests /pristine \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py
