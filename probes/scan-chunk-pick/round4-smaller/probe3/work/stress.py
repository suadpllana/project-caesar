import random
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p5_3/app")


def build(n_rows=60000, chunk_size=28, page_size=8, n_cond=8, seed=1):
    rnd = random.Random(seed)
    g = 25
    k = 1
    lines = [f"seg {g} {n_rows} {k}"]
    pos = 0
    while pos < n_rows:
        csize = min(chunk_size, n_rows - pos)
        ppos = 0
        pages = []
        while ppos < csize:
            psize = min(page_size, csize - ppos)
            vals = [rnd.randint(0, 2000) for _ in range(psize)]
            pages.append(vals)
            ppos += psize
        chunk_sum = sum(sum(p) for p in pages)
        lines.append(f"ch 0 p {chunk_sum}")
        for vals in pages:
            mn = min(vals)
            mx = max(vals)
            lines.append(
                f"pg {len(vals)} 0 {mn} {mx} e v " + " ".join(str(v) for v in vals)
            )
        pos += csize
    lines.append("qry")
    for i in range(n_cond):
        lines.append(f"prd le 0 {rnd.randint(0, 2000)}")
    lines.append("prj 0")
    lines.append("end")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import time

    import run_scan

    text = build()
    t0 = time.time()
    lines = run_scan.run(text)
    t1 = time.time()
    print("rows in output:", len(lines), "time:", t1 - t0)
