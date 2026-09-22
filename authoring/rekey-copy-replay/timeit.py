"""Time one implementation on the two large families. Output is the measurement, so flush."""
import sys
import time
from pathlib import Path

ROOT = Path("/home/user/project-caesar")
sys.path.insert(0, str(ROOT / "authoring" / "rekey-copy-replay"))
sys.path.insert(0, str(ROOT / "tasks" / "rekey-copy-replay" / "tests"))
import diff  # noqa: E402
import gen  # noqa: E402

which = sys.argv[1]
fams = sys.argv[2].split(",") if len(sys.argv) > 2 else ["wide", "deep"]
mod, _here = diff.loader(which)
work = [w for w in gen.programs("probe", 1) if w[0] in fams]
grand = 0.0
for fam, name, lines in work:
    text = "\n".join(lines) + "\n"
    t0 = time.time()
    out = mod.run(text)
    spent = time.time() - t0
    grand += spent
    print("%-10s %-10s %7d instructions %8d lines out %8.2fs" % (fam, name, len(lines), len(out), spent), flush=True)
print("total %.2fs" % grand, flush=True)
