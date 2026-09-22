FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN groupadd --gid 2201 dbgr && useradd --uid 2201 --gid 2201 --no-create-home --shell /usr/sbin/nologin dbgr
RUN groupadd --gid 2202 tgtr && useradd --uid 2202 --gid 2202 --no-create-home --shell /usr/sbin/nologin tgtr

RUN mkdir -p /app/dbg
RUN mkdir -p /logs/verifier

COPY . /tests/

RUN chmod 700 /tests/seal && chmod +x /tests/test.sh
