FROM python:3.12-slim

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The uid every line of agent code runs as. It gets a scratch pen at trial time and owns
# nothing else anywhere in this image.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# Artifacts land back at the absolute paths they were declared under, and the upload fails
# outright when the directory above one of them does not already exist.
RUN mkdir -p /app/pol

# tests/ is not copied in at trial time, so all of it is baked now: grader, sealed model,
# register generator, enumerated registers, their answers, and a copy of the tree as
# shipped. That copy is then moved off /tests, which puts it out of the run's reach by
# path and gives the grader something to weigh the executed tree against.
COPY . /tests/
RUN mv /tests/pristine /pristine

# What the run may read is decided here. It is welcome to runner.py, gen.py, cases.py,
# mark.py and reap.py: which registers get driven, and how the rest are built, is worth
# nothing without the seed, and the seed comes out of /dev/urandom once the agent has
# stopped. Which rows the grader weighs is another matter, so test_outputs.py is shut away
# beside the answers and the model.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
    && chmod 644 /tests/runner.py /tests/gen.py /tests/cases.py /tests/mark.py \
                 /tests/reap.py

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1
