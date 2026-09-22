#!/bin/bash
# leans on a file that is never collected
set -euo pipefail

cat > /app/rng/extra.py <<'PYEOF'
def fix(lines):
    return lines
PYEOF

python3 - <<'PYEOF'
import pathlib
p = pathlib.Path("/app/rng/ask.py")
s = p.read_text()
s = s.replace("from . import age, hole, knit, mend, out, pick",
              "from . import age, extra, hole, knit, mend, out, pick")
s = s.replace("    return lines", "    return extra.fix(lines)")
p.write_text(s)
PYEOF
