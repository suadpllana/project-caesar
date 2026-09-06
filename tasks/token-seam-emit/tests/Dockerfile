FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends util-linux \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN useradd --uid 1003 --user-group --no-create-home --shell /usr/sbin/nologin probe

RUN mkdir -p /app
RUN mkdir -p /app/strm

COPY . /tests/
COPY pristine/ /pristine/

RUN chmod 0755 /tests/test.sh
