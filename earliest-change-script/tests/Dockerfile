FROM python:3.13-slim-bookworm

RUN pip install pytest==9.1.1 pytest-json-ctrf==0.5.2

# pkill, for making sure nothing the sandbox started is still alive when the
# grading account takes over.
RUN apt-get update \
 && apt-get install -y procps util-linux \
 && rm -rf /var/lib/apt/lists/*

# sandbox  - runs the harness and its children, the only processes that import
#            the submitted module. It cannot read /tests, so the definitional
#            model and the answers are out of its reach.
# verifier - runs pytest and works out what the answers should have been. It
#            never imports the submitted module.
RUN useradd --create-home --uid 1002 --shell /usr/sbin/nologin sandbox \
 && useradd --create-home --uid 1001 --shell /usr/sbin/nologin verifier

COPY . /tests/

RUN mkdir -p /app
