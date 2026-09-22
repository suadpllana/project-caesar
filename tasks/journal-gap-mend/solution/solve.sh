#!/bin/bash
# Reference solution: the five files of the recovery tool, rewritten as one settle over the
# whole journal - forward over every line, backward from the final audit, then one walk per
# lost span. The source lives beside this script; this only puts it in place and runs the
# tool on two of the shipped journals.
set -euo pipefail

mine="$(cd "$(dirname "$0")" && pwd)"
for part in table tally span seek walk; do
  cp "${mine}/${part}.py" "/app/jl/${part}.py"
done

cd /app
python3 mend.py journals/small.txt
python3 mend.py journals/late.txt
