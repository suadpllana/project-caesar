FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/tests

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The harness does not copy tests/ at trial time; the grader, the sealed model, the case
# set, the generator, the ground truth and the untouched runtime tree all ride in here.
COPY . /tests/

# The untouched tree leaves /tests so the run cannot reach it by path.
RUN mv /tests/pristine /pristine

# The uid the run drops to.
RUN useradd -u 1003 -m -s /usr/sbin/nologin trail

# Only root reads the answers, the model and the grader; the run may read the runner,
# the case set and the generator, none of which yields a single trail without the nonce.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/reap.py

# The platform uploads each declared artifact to its absolute path; the parent has to
# exist first.
RUN mkdir -p /app/ui
