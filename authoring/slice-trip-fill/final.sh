#!/bin/bash
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "=== final differential: reference vs sealed model ==="
total=0
for s in f1 f2 f3 f4 f5 f6 f7 f8; do
  out=$(python3 -u diff.py $s 500 2>&1 | tail -1)
  echo "  $out"
  n=$(echo "$out" | sed -E 's/.*: ([0-9]+) sessions.*/\1/')
  total=$((total + n))
done
echo "  small sessions compared: $total"
echo "=== deep sessions, both shapes ==="
python3 -u - <<'PY'
import gen, model, readings, time
bad = 0
for nm, text in gen.deep_batch("finalcheck", 6):
    a = readings.run(readings.REFERENCE, text)
    b = [tuple(r) for r in model.solve(text)]
    ok = list(a) == b
    bad += 0 if ok else 1
    print("  %-16s rows=%7d agree=%s" % (nm, len(a), ok), flush=True)
print("  deep disagreements: %d" % bad)
PY
echo "=== reference through the real verifier at the full graded scale ==="
/usr/bin/time -f "  wall %e s" python3 -u trial.py --reference --small 300 --deep 4 2>&1 | tail -5
