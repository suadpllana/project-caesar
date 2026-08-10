FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
        python3 \
        python3-pip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

COPY . /tests/

RUN mkdir -p /app/svc/auth && cp -a /tests/app_pristine/. /app/

WORKDIR /tests
