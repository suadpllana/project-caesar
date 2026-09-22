#!/bin/bash
# The reference repair: the six model files, rewritten to the stated machine.
# Each file carries its own explanation; this script only puts them in place.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in line.py mem.py place.py turn.py step.py clock.py; do
  cp "${here}/${f}" "/app/sim/${f}"
done
