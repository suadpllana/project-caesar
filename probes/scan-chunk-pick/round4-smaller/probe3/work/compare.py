import sys
import time

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_3/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_3/work")

import run_scan
import brute


def extract(lines):
    out = []
    for ln in lines:
        f = ln.split()
        if f[0] == "sel":
            out.append(("sel", int(f[1]), int(f[2])))
        elif f[0] == "prj":
            out.append(("prj", int(f[1]), int(f[2]), int(f[3])))
    return out


def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    t0 = time.time()
    lines = run_scan.run(text)
    t1 = time.time()
    got = extract(lines)
    want = brute.run(text)
    t2 = time.time()
    ok = got == want
    print(path, "MATCH" if ok else "MISMATCH", "solver=%.3fs" % (t1 - t0), "brute=%.3fs" % (t2 - t1))
    if not ok:
        for i, (g, w) in enumerate(zip(got, want)):
            if g != w:
                print("  first mismatch at index", i, "got", g, "want", w)
                break
        if len(got) != len(want):
            print("  length mismatch: got", len(got), "want", len(want))
    # sanity: check dc/rd lines have no duplicates, and prints are well-formed
    seen_dc = set()
    seen_rd = set()
    dup = 0
    for ln in lines:
        f = ln.split()
        if f[0] == "dc":
            key = tuple(f[1:])
            if key in seen_dc:
                dup += 1
            seen_dc.add(key)
        elif f[0] == "rd":
            key = tuple(f[1:])
            if key in seen_rd:
                dup += 1
            seen_rd.add(key)
    if dup:
        print("  DUPLICATE dc/rd prints:", dup)
    return ok


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
