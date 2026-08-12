FROM python:3.12-slim

# The verifier owns its own copy of everything it needs: the tests, the sealed trainer,
# the scenario set, the ground truth, and a pristine copy of the tree. The agent's
# declared files are overlaid onto that pristine copy at trial time, so edits outside the
# declared set never reach the run.
COPY . /tests/

RUN cp -a /tests/pristine /pristine \
    && rm -rf /tests/pristine

# The harness uploads the declared artifacts at their original absolute paths.
RUN mkdir -p /app/train /app/data

RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

# The unprivileged uid the trainer run drops to. It can write its work directory and
# nothing else that matters.
RUN useradd -u 1002 -m -s /usr/sbin/nologin sandbox

# The ground truth and the sealed trainer are readable by root only. The run imports
# scen.py, which is fine: knowing which op sequences execute does not produce the
# parameter vectors they end on.
RUN chmod 755 /tests \
    && chmod 600 /tests/gt.json /tests/oracle.py \
    && chmod 644 /tests/scen.py /tests/runner.py /tests/reap.py /tests/train.json

ENV PYTHONPATH=/tests
ENV PYTHONDONTWRITEBYTECODE=1
