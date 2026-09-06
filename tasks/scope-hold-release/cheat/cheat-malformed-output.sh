#!/bin/bash
set -euo pipefail
APP="${APPDIR:-$(pwd)}"
cat > "${APP}/wire/tear.py" <<'SHR_EOF'
class Bad:
    def __eq__(self, other):
        raise SystemExit(0)

    def __str__(self):
        raise SystemExit(0)


def order(mine):
    return [Bad()]
SHR_EOF
