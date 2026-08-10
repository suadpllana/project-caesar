#!/bin/bash
set -euo pipefail

mkdir -p /app
cp "$(dirname "$0")/file_reads.py" /app/file_reads.py
