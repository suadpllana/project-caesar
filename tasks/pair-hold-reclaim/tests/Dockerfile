FROM python:3.12-slim

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# The harness re-materialises every declared artifact at its own absolute path, so the
# parent has to be there before that upload runs. It stays on a line of its own: the
# structural check reads RUN instructions line by line and does not join continuations.
RUN mkdir -p /app/core

RUN useradd --uid 1002 --create-home sandbox \
 && mkdir -p /work /rep /logs/verifier

COPY . /tests/

RUN cp -a /tests/pristine /pristine \
 && chmod 700 /rep \
 && chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py \
 && chmod 755 /tests/test.sh /tests/reap.py

WORKDIR /tests
