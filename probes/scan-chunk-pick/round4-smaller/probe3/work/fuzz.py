import sys
import traceback

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_3/app")
sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_3/work")

import gen
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


def check_dc_rd(lines):
    seen = set()
    for ln in lines:
        f = ln.split()
        if f[0] in ("dc", "rd"):
            key = (f[0], tuple(f[1:]))
            if key in seen:
                return False, "duplicate " + ln
            seen.add(key)
    return True, None


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    fails = 0
    for seed in range(trials):
        text = gen.gen(seed)
        try:
            lines = run_scan.run(text)
        except Exception:
            fails += 1
            print("SEED", seed, "EXCEPTION")
            print(text)
            traceback.print_exc()
            if fails > 3:
                break
            continue
        got = extract(lines)
        want = brute.run(text)
        ok_dc, msg = check_dc_rd(lines)
        if got != want or not ok_dc:
            fails += 1
            print("SEED", seed, "MISMATCH" if got != want else "DUP", msg or "")
            print(text)
            print("got: ", got)
            print("want:", want)
            if fails > 5:
                break
    print("done, fails=", fails, "of", trials)
    return fails == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
