import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/work")

import run_scan
import brute


def keyed(lines):
    return [l for l in lines if l.startswith("qry") or l.startswith("sel") or l.startswith("prj")]


def check(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    a = run_scan.run(text)
    b = brute.run(text)
    ka, kb = keyed(a), keyed(b)
    if ka != kb:
        print("MISMATCH in", path)
        for i, (x, y) in enumerate(zip(ka, kb)):
            if x != y:
                print("  line", i, "impl:", x, " brute:", y)
        if len(ka) != len(kb):
            print("  length differs:", len(ka), "vs", len(kb))
        return False
    print("OK (final results match)", path, "-", len(ka), "sel/prj/qry lines")
    return True


if __name__ == "__main__":
    ok = True
    for p in sys.argv[1:]:
        ok = check(p) and ok
    sys.exit(0 if ok else 1)
