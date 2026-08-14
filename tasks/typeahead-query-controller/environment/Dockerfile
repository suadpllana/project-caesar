FROM node:22-bookworm-slim

# Unpinned apt packages by policy; clean up the lists afterwards.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so the layer caches independently of source.
COPY app/package.json app/package-lock.json ./
RUN npm ci

COPY app/tsconfig.json app/vite.config.ts app/README.md ./
COPY app/src ./src
COPY app/public ./public

# The agent edits files under /app/src. The dev server is started by the
# agent (npm run dev) and by the conformance driver.
EXPOSE 5173

CMD ["sleep", "infinity"]
