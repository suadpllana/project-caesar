import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_3/work")

import gen
import run_scan
import ref2


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    fails = 0
    for seed in range(n):
        text = gen.gen(seed)
        try:
            a = run_scan.run(text)
        except Exception as e:
            print("seed", seed, "impl CRASHED:", repr(e))
            fails += 1
            continue
        try:
            b = ref2.run(text)
        except Exception as e:
            print("seed", seed, "ref2 CRASHED:", repr(e))
            fails += 1
            continue
        if a != b:
            print("seed", seed, "FULL TRACE MISMATCH")
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print("  line", i, "impl:", x, " ref2:", y)
            if len(a) != len(b):
                print("  length differs:", len(a), "vs", len(b))
            fails += 1
    print("done:", n, "seeds,", fails, "failures")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
