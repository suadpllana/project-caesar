FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
        python3 \
        ca-certificates \
        curl \
        vim \
        less \
    && rm -rf /var/lib/apt/lists/*

COPY app_src/ /app/

WORKDIR /app
