#!/usr/bin/env python3
"""Which graded field actually separates each cheat from the reference.

The run audit flagged the `evict` counter: it records when the index happens to drop a
stale entry, which is a free implementation choice rather than a measure of work, so a
correct solution that retires entries eagerly instead of lazily fails on it. Before
removing it from the graded set this reports, per cheat, which fields diverge - so the
change can be made knowing exactly what discriminating power it costs.

Usage:  python3 authoring/field_report.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
EDITABLE = ["model/pstore.py", "runtime/pfx.py", "runtime/sch.py", "mem/pool.py"]
FIELDS = ("computed", "reused", "pos", "preempt", "evict", "restart")


def bash() -> str:
    """A bash that can actually run the cheat scripts.

    On Windows the name `bash` on PATH is usually the WSL stub, which exits 1 without
    running anything when no distribution is installed - every cheat then silently
    no-ops and the whole report measures the shipped tree over and over.  Prefer a real
    Git Bash when one is present.
    """
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files\Git\usr\bin\bash.exe"):
        if Path(cand).is_file():
            return cand
    found = shutil.which("bash")
    if found is None:
        raise SystemExit("no bash on PATH; cannot replay the cheat scripts")
    return found


def run(script: Path | None) -> dict:
    """Play one cheat against a throwaway copy of the shipped tree, then grade it.

    The cheat scripts write to the absolute path /app, which is where the agent lands
    inside the container.  Off a Linux host that path is not writable, so the script is
    replayed against a temporary directory with /app rewritten to it.  The shipped
    scripts are never modified; only the copy handed to bash is.
    """
    with tempfile.TemporaryDirectory() as tmp:
        live = Path(tmp) / "live"
        shutil.copytree(TASK / "environment" / "app_src", live)
        if script is not None:
            body = script.read_text().replace("/app", live.as_posix())
            play = Path(tmp) / script.name
            play.write_text(body, newline="\n")
            proc = subprocess.run([bash(), str(play)], capture_output=True, cwd=tmp)
            if proc.returncode != 0:
                print("  ! %s exited %d: %s" % (
                    script.name, proc.returncode,
                    proc.stderr.decode("utf-8", "replace")[-200:]), file=sys.stderr)
        app = Path(tmp) / "app"
        shutil.copytree(TASK / "tests" / "pristine", app)
        for rel in EDITABLE:
            if (live / rel).is_file():
                shutil.copyfile(live / rel, app / rel)
        out = Path(tmp) / "out.json"
        env = dict(os.environ)
        env.update({"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1"})
        subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                       capture_output=True, env=env, timeout=900)
        try:
            return json.loads(out.read_text())
        except (OSError, ValueError):
            return {"reports": {}, "errors": {"fatal": "no output"}}


def main() -> int:
    gt = json.loads((TASK / "tests" / "gt.json").read_text())["scenarios"]
    names = list(gt)

    for script in [None] + sorted((TASK / "cheat").glob("*.sh")):
        label = script.name if script else "nop"
        data = run(script)
        reps = data.get("reports", {})
        diff = {f: [] for f in FIELDS}
        tokens_bad = []
        for name in names:
            want = gt[name]["report"]
            got = reps.get(name)
            if not isinstance(got, dict):
                for f in FIELDS:
                    diff[f].append(name)
                tokens_bad.append(name)
                continue
            if got.get("out") != want["out"]:
                tokens_bad.append(name)
            for f in FIELDS:
                if got.get(f) != want[f]:
                    diff[f].append(name)
        only_evict = (diff["evict"] and not tokens_bad
                      and not any(diff[f] for f in FIELDS if f != "evict"))
        print("%-34s tokens:%-2d %s%s" % (
            label, len(tokens_bad),
            " ".join("%s:%d" % (f, len(diff[f])) for f in FIELDS),
            "   <-- SEPARATED ONLY BY evict" if only_evict else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
