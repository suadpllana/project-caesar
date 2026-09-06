#!/bin/bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
cp "${here}/keep.py" /app/cyc/keep.py
cd /app
python run_prog.py progs/small.txt
