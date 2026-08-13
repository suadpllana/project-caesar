#!/usr/bin/env bash
# Reference solution: install the corrected controller.
#
# Only src/controller.ts is replaced -- the shared contract, the test
# transport and the harness are left exactly as shipped, which is also what
# the verifier's integrity check requires.
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "${HERE}/controller.ts" "${APP_DIR}/src/controller.ts"

echo "[solve] installed reference controller at ${APP_DIR}/src/controller.ts"
