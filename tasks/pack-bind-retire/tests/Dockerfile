FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

RUN groupadd --gid 1007 walker
RUN useradd --uid 1007 --gid 1007 --no-create-home --shell /usr/sbin/nologin walker

RUN mkdir -p /app
RUN mkdir -p /app/hst
RUN mkdir -p /lab

WORKDIR /tests

COPY . /tests/
COPY pristine/ /pristine/

RUN chmod 0755 /tests/test.sh
