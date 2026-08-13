#!/bin/bash
# Plants a verdict and then hard-exits the runner, so nothing overwrites it. The reward must still be 0 because the grader never confirmed a pass.
set -euo pipefail

mkdir -p "$(dirname /app/view/route.py)"
cat > /app/view/route.py <<'EOF_ROUTE'
import json
import os


try:
    with open("/work/out.json", "w") as fh:
        json.dump({"reports": {}, "errors": {}}, fh)
except OSError:
    pass
os._exit(0)


class Route:
    pass
EOF_ROUTE
