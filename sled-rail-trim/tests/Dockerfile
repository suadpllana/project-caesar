FROM debian:bookworm-slim

# setpriv comes from util-linux, pgrep/pkill from procps. Apt packages are
# never pinned; the lists are cleaned up straight after.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential python3 python3-pip util-linux procps ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/bin/python3 /usr/local/bin/python

# Everything the verifier needs is baked in here. test.sh installs nothing.
RUN pip3 install --no-cache-dir --break-system-packages \
      pytest==9.1.1 \
      pytest-json-ctrf==0.5.2

# The account the apply path is compiled and run under. It owns nothing and can
# read nothing it was not handed.
RUN useradd --system --create-home --home-dir /home/verifier \
      --shell /usr/sbin/nologin verifier

COPY . /tests/

# Fail the build rather than the run if any of the pieces went missing.
RUN test -f /tests/runner/runner.c \
 && test -f /tests/part.py \
 && test -f /tests/plan.py \
 && test -f /tests/sessions.py \
 && test -f /tests/harness.py \
 && test -f /tests/pristine/include/sled.h \
 && test -f /tests/pristine/src/sandbox.c \
 && test -f /tests/pristine/Makefile

# The part model, the sessions and the ceiling all sit in here. Root only, so
# the account the runner uses cannot go looking for the answers instead of
# spending fewer transactions. The two pieces the compiler has to read are
# published outside it.
RUN mkdir -p /probe/include \
 && cp /tests/runner/runner.c /probe/runner.c \
 && cp /tests/pristine/include/sled.h /probe/include/sled.h \
 && chmod -R a+rX /probe

RUN chmod -R go-rwx /tests \
 && chmod 755 /tests/test.sh

# Pre-create the parent directory of every declared artifact, or harbor's upload
# fails with "Could not find the file /app in container".
RUN mkdir -p /app/src /logs/verifier

WORKDIR /tests
