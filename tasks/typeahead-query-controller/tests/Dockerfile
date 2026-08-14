FROM node:22-bookworm-slim

# --- system deps (unpinned by policy) --------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      procps \
      util-linux \
      python3 \
      python3-pip \
      python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Unprivileged account used to run the dev server, which evaluates code
# derived from the agent's tree. It must never be able to reach the reward
# channel, so grading stays root-only.
RUN useradd --system --create-home --shell /usr/sbin/nologin verifier

# --- python verifier tooling ------------------------------------------------
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2

# --- node verifier tooling --------------------------------------------------
# Vite serves the agent's source; Playwright drives a real browser. Installed
# here so test.sh never installs anything at verify time.
WORKDIR /verifier
RUN npm init -y >/dev/null 2>&1 \
    && npm install --no-audit --no-fund \
       vite@5.4.10 \
       typescript@5.6.3 \
       playwright@1.48.2

# Chromium + its OS libraries. The driver runs as root, so a shared location
# keeps the browser out of any per-user cache.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN npx --yes playwright@1.48.2 install --with-deps chromium \
    && chmod -R a+rX /ms-playwright \
    && rm -rf /var/lib/apt/lists/*

ENV NODE_PATH=/verifier/node_modules

# --- tests ------------------------------------------------------------------
# harbor does NOT upload tests/ at verify time: bake them in.
COPY . /tests/
RUN chmod +x /tests/test.sh

# Pristine copies of the files the agent must not modify (baked via COPY .
# above, under /tests/pristine) are used for the integrity check. They live
# inside the verifier image so they cannot be tampered with from the
# environment. Fail the build early if they went missing.
RUN test -f /tests/pristine/src/types.ts \
    && test -f /tests/pristine/src/transport.ts \
    && test -f /tests/pristine/src/main.ts \
    && test -f /tests/pristine/vite.config.ts \
    && test -f /tests/pristine/tsconfig.json \
    && test -f /tests/pristine/package.json \
    && test -f /tests/pristine/public/index.html

# The dev server runs as `verifier`, so the toolchain must be readable by it
# -- but writable by nobody except root.
RUN chmod -R a+rX /verifier /tests

# Pre-create the parent dir of every declared artifact, or harbor's upload
# fails with "Could not find the file /app in container".
RUN mkdir -p /app/src /app/public /logs/verifier

WORKDIR /tests
