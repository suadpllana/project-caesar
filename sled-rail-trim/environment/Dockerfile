FROM debian:bookworm-slim

# No pins on apt packages by policy; the lists go straight afterwards.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential ca-certificates git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/

CMD ["sleep", "infinity"]
