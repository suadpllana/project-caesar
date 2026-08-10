FROM python:3.13-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends util-linux procps \
 && rm -rf /var/lib/apt/lists/*

RUN pip install pytest==9.1.1 pytest-json-ctrf==0.5.2

# sandbox - runs the harness and the child that imports the submitted planner.
#           It cannot read /tests, so the definitional model is out of reach.
# grading - runs pytest and works out the right answers. It never imports
#           submitted code.
RUN useradd --create-home --uid 1002 --shell /usr/sbin/nologin sandbox \
 && useradd --create-home --uid 1001 --shell /usr/sbin/nologin grading

COPY . /tests/

RUN mkdir -p /app /logs/verifier
