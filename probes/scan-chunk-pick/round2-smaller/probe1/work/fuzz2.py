import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/work")

import gen2
import fuzz
import brute


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    max_cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    fails = 0
    for seed in range(n_trials):
        text = gen2.gen_file(seed, n_rows_max=max_rows, n_cols=max_cols, n_queries=4)
        try:
            real_lines = fuzz.real_run(text)
        except Exception as e:
            print("SEED %d: real impl raised %r" % (seed, e))
            print(text)
            fails += 1
            continue
        try:
            brute_lines = brute.run(text)
        except Exception as e:
            print("SEED %d: brute raised %r" % (seed, e))
            print(text)
            fails += 1
            continue

        real_filtered = fuzz.filter_sel_prj(real_lines)
        if real_filtered != brute_lines:
            print("SEED %d MISMATCH" % seed)
            print("---- input ----")
            print(text)
            print("---- real (filtered) ----")
            print("\n".join(real_filtered))
            print("---- brute ----")
            print("\n".join(brute_lines))
            print("---- real full ----")
            print("\n".join(real_lines))
            fails += 1
            if fails > 5:
                break
            continue

        from scn import parse
        seg, queries = parse.load(text)
        try:
            fuzz.check_trace_sanity(seg, queries, real_lines)
        except AssertionError as e:
            print("SEED %d TRACE SANITY FAIL: %s" % (seed, e))
            print(text)
            print("\n".join(real_lines))
            fails += 1
            if fails > 5:
                break

    print("done: %d trials, %d fails" % (n_trials, fails))


if __name__ == "__main__":
    main()
