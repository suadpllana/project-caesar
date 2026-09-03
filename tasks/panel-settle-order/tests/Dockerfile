FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

# The uid the run drops to before a line of the submission is executed. It owns its own
# work copy of the engine and nothing else in the image.
RUN useradd --uid 1002 --create-home --shell /usr/sbin/nologin sandbox

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The harness re-materialises each declared artifact at the absolute path it had in the
# agent's container, so those parents have to exist before the upload happens. /rep holds
# the run's report and is root-only: the uid that executes the submission writes into it
# through an inherited descriptor and can never reopen it by name.
RUN mkdir -p /app/pnl /work /rep /logs/verifier && chmod 700 /rep

# Nothing is fetched at trial time. Everything the verifier needs is baked here, because
# the harness does not copy tests/ into this container when the trial runs.
COPY . /tests/

# The untouched engine moves out of /tests so the run cannot reach it by path, and so the
# grader has something to compare the executed tree against that the run could not write.
RUN mv /tests/pristine /pristine

# The model, the answers and the grader are root-only. The run is welcome to read the
# runner, the generator and the enumerated panels: knowing which panels execute, and how
# the rest are built, yields not one of their ledgers, because the seed is made from
# /dev/urandom after the submission has stopped. Which rows the grader compares would be a
# different matter, so test_outputs.py is sealed alongside the answers.
RUN chmod 755 /tests \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py \
 && chmod 755 /tests/test.sh /tests/reap.py

WORKDIR /tests
