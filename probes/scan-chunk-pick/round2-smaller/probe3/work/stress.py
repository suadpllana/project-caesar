import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/work")

import gen
import run_scan
import brute


def keyed(lines):
    return [l for l in lines if l.startswith("qry") or l.startswith("sel") or l.startswith("prj")]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    fails = 0
    for seed in range(n):
        text = gen.gen(seed)
        try:
            a = run_scan.run(text)
        except Exception as e:
            print("seed", seed, "CRASHED:", repr(e))
            fails += 1
            continue
        b = brute.run(text)
        ka, kb = keyed(a), keyed(b)
        if ka != kb:
            print("seed", seed, "MISMATCH")
            for i, (x, y) in enumerate(zip(ka, kb)):
                if x != y:
                    print("  line", i, "impl:", x, " brute:", y)
            if len(ka) != len(kb):
                print("  length differs:", len(ka), "vs", len(kb))
            fails += 1
    print("done:", n, "seeds,", fails, "failures")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
