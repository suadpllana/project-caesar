#!/usr/bin/env bash
# Reference apply path. Replaces the driver with one that works out what the
# batch actually needs, says both halves of a rail's trim in one pair word
# wherever the part will take one, puts every trim behind a single mode change,
# never takes down a rail the batch leaves in service, leads each mode window
# with a frame so the settling costs nothing, and stages neighbouring registers
# in one frame wherever that is cheaper and the part will take it.
set -euo pipefail

install -m 644 "$(dirname "$0")/driver.c" /app/src/driver.c

cd /app && make sandbox >/dev/null && spent=$(./sandbox | tail -1)
echo "apply path replaced; the sandbox batch now costs: ${spent}"
