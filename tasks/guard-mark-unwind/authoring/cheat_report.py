"""Which assertion catches each cheat.

A cheat that scores 0 proves nothing until you know why. The failure has to be on the
axis the cheat was aimed at: a probe that dies on an import error has been rejected by
nothing, and a single-mistake cheat that fails the integrity checks rather than the model
comparison is testing the wrong thing.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    cd = os.path.join(ROOT, "cheat")
    work = tempfile.mkdtemp(prefix="gmu-report-")
    bad = 0
    for name in sorted(os.listdir(cd)):
        if not name.endswith(".sh"):
            continue
        d = os.path.join(work, name[:-3])
        os.makedirs(d)
        env = dict(os.environ)
        env["APP"] = os.path.join(d, "app")
        subprocess.run(["bash", os.path.join(cd, name)], cwd=d, env=env,
                       capture_output=True, text=True)
        src = os.path.join(d, "app", "kern")
        rc = subprocess.run([sys.executable, os.path.join(HERE, "trial.py"),
                             "--dir", src if os.path.isdir(src) else d],
                            capture_output=True, text=True)
        out = rc.stdout
        m = re.search(r"reward (\d)\s*(.*)", out)
        reward = int(m.group(1)) if m else 1
        fired = sorted(set((m.group(2) if m else "").split())
                       | set(re.findall(r"::(test_\w+)", out)))
        print("%-30s reward %d   %s" % (name[:-3], reward, " ".join(fired) or "-"))
        if reward or not fired:
            bad += 1
    shutil.rmtree(work, ignore_errors=True)
    print("%s" % ("every cheat rejected, and on an axis"
                  if not bad else "%d CHEATS NEED A LOOK" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
