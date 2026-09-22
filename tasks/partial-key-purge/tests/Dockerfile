# Grading image. It carries the grader's pinned tools, a uid for running submitted code with no
# rights over the answers or the reward, and the tests themselves: in separate mode the harness
# does not copy tests/ in, so they are baked here.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends util-linux procps \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2
RUN useradd --uid 1002 --create-home sandbox
RUN mkdir -p /app/db /work /logs/verifier

COPY . /tests/
RUN chmod 700 /tests/seal && chmod 755 /tests/test.sh
