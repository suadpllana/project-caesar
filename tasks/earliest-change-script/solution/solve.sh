#!/bin/bash
set -euo pipefail

mkdir -p /app
cp "$(dirname "$0")/change_script.py" /app/change_script.py
