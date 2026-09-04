#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-/app}"
cp "${HERE}/board.py" "${APP_DIR}/note/board.py"
cp "${HERE}/rule.py"  "${APP_DIR}/note/rule.py"
