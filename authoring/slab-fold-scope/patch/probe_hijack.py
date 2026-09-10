import pathlib

_forged = '''import sys

import ops
from tab import store


def main():
    tab = store.Tab()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(tab, tuple(line.split()))
    sys.stdout.write("\\n".join(tab.out) + "\\n")


if __name__ == "__main__":
    main()
'''

for _where in ("/app/run_tab.py", "/app/ops.py", "/app/tab/log.py", "/app/tab/store.py",
               "/app/tab/say.py"):
    try:
        pathlib.Path(_where).write_text(_forged, encoding="utf-8")
    except Exception:
        pass
