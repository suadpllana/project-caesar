FROM python:3.12-slim

# Everything the verifier needs is installed here. Nothing is fetched at trial time.
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/tests

# In separate mode the harness uploads no tests, so the grader, the sealed model, the
# ground truth, the case set, the generator and the untouched engine all ride in the image.
COPY . /tests/

# The untouched engine is moved out of /tests: the run may read /tests, and the copy it is
# graded against must not be reachable by a path the run can open.
RUN mv /tests/pristine /pristine

# The account the run drops to. It owns nothing under /tests, /pristine or /logs.
RUN useradd --uid 1004 --no-create-home --shell /usr/sbin/nologin sweep

# The answers, the model and the grader are root's alone; the runner, the case set and the
# generator stay readable, and none of them yields a graded line without the run's nonce.
RUN chmod 755 /tests \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py

# Declared artifacts are uploaded to their original absolute paths, so the parent has to
# be there before verification starts.
RUN mkdir -p /app/sheet
