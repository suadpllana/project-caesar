FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
        python3 \
        python3-pip \
        ca-certificates \
        util-linux \
        procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --break-system-packages \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2

COPY . /tests/

RUN mkdir -p /app/svc/auth && cp -a /tests/app_pristine/. /app/

# The application tree is read-only to the unprivileged user that executes the agent's
# code, and the test suite is not readable by it at all (tests/test.sh tightens /tests
# further at run time, after copying the sandboxed worker out to /run).
RUN chown -R root:root /app && chmod -R u+rwX,go-w,go+rX /app \
    && chown -R root:root /tests && chmod -R go-rwx /tests

WORKDIR /tests
