#!/bin/bash
# The reference determination. The four files it installs sit beside this script.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APPDIR:-/app}"

for f in screen.py voice.py tally.py note.py; do
  cp "${HERE}/${f}" "${APP}/pol/${f}"
done

cd "${APP}"
python screen_reg.py regs/plain.txt regs/share.txt regs/ring.txt
