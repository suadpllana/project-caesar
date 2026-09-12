#!/bin/bash
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in hold want pull place prune wire; do
  cp "${mine}/${part}.py" "/app/bind/${part}.py"
done

cd /app
python run_bind.py progs/one.txt
python run_bind.py progs/two.txt
