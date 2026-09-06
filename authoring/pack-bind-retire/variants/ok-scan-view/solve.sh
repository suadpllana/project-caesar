#!/bin/bash
set -Eeuo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in vw.py bd.py ld.py rt.py od.py; do
  cp "$here/$f" "/app/hst/$f"
done

cd /app
python run_host.py cases/boot.txt cases/swap.txt cases/chain.txt > /dev/null
