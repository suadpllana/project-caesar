"""Time one set of the six files on one program, inside the process that runs it.

Output is flushed as it goes: a timing harness whose output sits in a buffer behind the slow
case looks exactly like a hang, and that has cost a session before.

    python authoring/bind-claim-prune/time_one.py <ref|env|dir> <prog> [<prog> ...]
"""
import pathlib
import resource
import subprocess
import shutil
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lab  # noqa: E402

DRIVE = """
import resource, sys, time
sys.path.insert(0, %r)
import ops
from bind import book
job = book.Job()
t = time.time()
with open(%r, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            ops.ex(job, tuple(line.split()))
sys.stderr.write("%%.2f s  %%d MB\\n" %% (
    time.time() - t, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024))
sys.stdout.write("\\n".join(job.out[-3:]) + "\\n")
"""


def main():
    which = sys.argv[1]
    app = lab.tree(which)
    for prog in sys.argv[2:]:
        code = DRIVE % (str(app), str(pathlib.Path(prog).resolve()))
        t = time.time()
        got = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             timeout=float(sys.argv[0] and 1800))
        print("%-28s wall %6.2f s  %s" % (pathlib.Path(prog).name, time.time() - t,
                                          got.stderr.strip().replace("\n", " | ")), flush=True)
        print("   tail: %s" % got.stdout.strip().replace("\n", " / "), flush=True)
    shutil.rmtree(app.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
