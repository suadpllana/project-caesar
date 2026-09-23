import sys
import traceback

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_2/work")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_2/app")

import gen
import run_scan
import brute


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    fails = 0
    for seed in range(start, start + n):
        text = gen.gen(seed, n_max=250, k_max=6)
        try:
            real = run_scan.run(text)
        except Exception:
            print("SEED %d: real implementation crashed" % seed)
            print(text)
            traceback.print_exc()
            fails += 1
            continue
        try:
            bru = brute.run(text)
        except Exception:
            print("SEED %d: brute implementation crashed" % seed)
            fails += 1
            continue
        real_num = [l for l in real if l.startswith("sel") or l.startswith("prj")]
        bru_num = [l for l in bru if l.startswith("sel") or l.startswith("prj")]
        if real_num != bru_num:
            print("SEED %d: MISMATCH" % seed)
            print(text)
            print("real:", real_num)
            print("brute:", bru_num)
            fails += 1
        seen_dc = set()
        seen_rd = set()
        for l in real:
            f = l.split()
            if f[0] == "dc":
                key = tuple(f[1:])
                assert key not in seen_dc, ("dup dc", seed, key)
                seen_dc.add(key)
            elif f[0] == "rd":
                key = tuple(f[1:])
                assert key not in seen_rd, ("dup rd", seed, key)
                seen_rd.add(key)
    print("done. seeds=%d fails=%d" % (n, fails))


if __name__ == "__main__":
    main()
