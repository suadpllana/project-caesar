import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/work")

import importlib

import gen
import brute

APP = "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p6_1/app"


def real_run(text):
    # Fresh import each time isn't necessary since state is not module-global,
    # but re-import to be safe against any accidental caching in the impl.
    import run_scan
    importlib.reload(run_scan)
    return run_scan.run(text)


def filter_sel_prj(lines):
    return [l for l in lines if l.startswith("qry") or l.startswith("sel") or l.startswith("prj")]


def check_trace_sanity(seg, queries, lines):
    """Sanity-check the dc/rd/prj trace structurally: every dc/rd references a
    real chunk, no chunk is dc'd or rd'd more than once per query, dc always
    fires before a prj/sel needs it is not checked here (too strong), but we
    do check dc implies the chunk was not previously *only* rd'd twice etc."""
    qi = -1
    seen_dc = set()
    seen_rd = set()
    for line in lines:
        parts = line.split()
        tag = parts[0]
        if tag == "qry":
            qi = int(parts[1])
            seen_dc = set()
            seen_rd = set()
        elif tag == "dc":
            c, j = int(parts[1]), int(parts[2])
            assert 0 <= c < seg.k, line
            assert 0 <= j < len(seg.cols[c]), line
            key = (c, j)
            assert key not in seen_dc, "duplicate dc in one query: %s" % line
            seen_dc.add(key)
        elif tag == "rd":
            c, j = int(parts[1]), int(parts[2])
            assert 0 <= c < seg.k, line
            assert 0 <= j < len(seg.cols[c]), line
            key = (c, j)
            assert key not in seen_rd, "duplicate rd in one query: %s" % line
            seen_rd.add(key)


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    max_cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    fails = 0
    for seed in range(n_trials):
        text = gen.gen_file(seed, n_rows_max=max_rows, n_cols=max_cols,
                             n_queries=3)
        try:
            real_lines = real_run(text)
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

        real_filtered = filter_sel_prj(real_lines)
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

        # structural sanity check on the trace
        from scn import parse
        seg, queries = parse.load(text)
        try:
            check_trace_sanity(seg, queries, real_lines)
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
