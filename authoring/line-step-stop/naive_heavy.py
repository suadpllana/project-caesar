"""Time a single-stepping engine on one frozen heavy session, through the real link.

    python naive_heavy.py VARIANT_DIR HEAVY_NAME [CAP_SECONDS]

cheat_report.py only shows the first session that stops a slow engine, and for both slow
variants that is sample-long, which the agent has. This measures a frozen heavy session the
agent never sees, so the claim that the heavy set alone would stop a single-stepping engine is
a number rather than an estimate. Everything is written to a temporary directory outside the
bundle.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from lab import APP, SEAL, SOL

FILES = ("frames.py", "marks.py", "steps.py")


def main():
    variant, name = sys.argv[1], sys.argv[2]
    cap = float(sys.argv[3]) if len(sys.argv) > 3 else 400.0
    gt = json.load(open(os.path.join(SEAL, "gt.json")))
    s = next(x for x in gt["heavy"] if x["name"] == name)
    work = tempfile.mkdtemp(prefix="lss-naive-")
    try:
        app = os.path.join(work, "app")
        shutil.copytree(APP, app)
        for f in FILES:
            # a variant carries only the files it changes; the rest are the reference's
            src = os.path.join(variant, f)
            shutil.copy(src if os.path.exists(src) else os.path.join(SOL, f), os.path.join(app, "dbg", f))
        for ext, body in (("img", s["image"]), ("cmd", "\n".join(s["cmds"]) + "\n"),
                          ("tape", " ".join(str(v) for v in s["tape"]) + "\n")):
            with open(os.path.join(work, "p." + ext), "w", newline="\n") as fh:
                fh.write(body)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        t0 = time.monotonic()
        try:
            r = subprocess.run([sys.executable, os.path.join(app, "run_dbg.py"),
                                os.path.join(work, "p.img"), os.path.join(work, "p.cmd"),
                                os.path.join(work, "p.tape")],
                               capture_output=True, text=True, timeout=cap, env=env)
            secs = time.monotonic() - t0
            got = r.stdout.splitlines()
            verdict = "finished, %s" % ("lines match" if got == s["want"] else "LINES DIFFER")
            if got != s["want"]:
                sys.stderr.write(r.stderr[-2000:])
        except subprocess.TimeoutExpired:
            secs = time.monotonic() - t0
            verdict = "cut off at the cap"
        print(json.dumps({"variant": os.path.basename(os.path.normpath(variant)), "session": name,
                          "in_frame": s["in_frame"], "volume": s["volume"],
                          "seconds": round(secs, 1), "cap": cap, "result": verdict}), flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
