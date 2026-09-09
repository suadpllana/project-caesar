"""Time the four semantically-correct-but-slow readings against the reference."""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
import mkoverlay  # noqa: E402

rows = [("reference", str(HERE.parents[1] / "tasks" / "publish-settle-order" / "solution"))]
for name in ("scan-the-order", "global-list-filtered", "want-scan", "sweep-rescan"):
    rows.append((name, str(mkoverlay.build(HERE / "readings" / name))))

for name, where in rows:
    out = subprocess.run([sys.executable, "-u", str(HERE / "time_all.py"), where],
                         capture_output=True, text=True, timeout=7200).stdout
    got = {ln.split()[0]: ln.split()[1] for ln in out.strip().splitlines() if len(ln.split()) == 2}
    print("%-22s wide %-9s tear %-9s total %s"
          % (name, got.get("wide", "-"), got.get("tear", "-"), got.get("total", "-")), flush=True)
