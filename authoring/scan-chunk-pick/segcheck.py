"""Check that a segment file is one the writer could have produced.

Every hand-written file goes through this before it is frozen: a chunk's sum is the sum of the
non-null values of its pages, a page's null count and recorded pair are what its values give
(rounded inward to a multiple of the granularity under `w`), index pages sit only in dictionary
chunks and index inside the dictionary, the dictionary is ascending, pages cover the rows, and
every query names a condition and a column. A file that fails here is not a file the brief
describes, and a case built on it would grade something that is not the task.
"""
import sys


def check(text):
    errs = []
    lines = [ln for ln in text.split("\n") if ln.strip()]
    f = lines[0].split()
    if f[0] != "seg":
        return ["no seg line"]
    g, n, k = int(f[1]), int(f[2]), int(f[3])
    rows = [0] * k
    ch = None
    pages = []

    def close():
        if ch is None:
            return
        total = 0
        for vals in pages:
            total += sum(v for v in vals if v is not None)
        if total != ch["sum"]:
            errs.append("chunk %d/%d sum %d, pages sum to %d" % (ch["c"], ch["j"], ch["sum"], total))

    counts = [0] * k
    qn = None
    for ln in lines[1:]:
        f = ln.split()
        if f[0] == "ch":
            close()
            c = int(f[1])
            dic = None
            if f[2] == "d":
                m = int(f[4])
                dic = [int(t) for t in f[5:5 + m]]
                if len(f) != 5 + m:
                    errs.append("chunk line length: %s" % ln)
                if dic != sorted(set(dic)):
                    errs.append("dictionary not ascending and distinct: %s" % ln)
            elif len(f) != 4:
                errs.append("plain chunk line: %s" % ln)
            ch = {"c": c, "j": counts[c], "sum": int(f[3]), "dic": dic, "forms": []}
            counts[c] += 1
            pages = []
        elif f[0] == "pg":
            m, u = int(f[1]), int(f[2])
            form = f[6]
            toks = f[7:]
            if len(toks) != m:
                errs.append("page length: %s" % ln)
            if form == "i" and ch["dic"] is None:
                errs.append("index page in a plain chunk: %s" % ln)
            if form == "i" and ch["forms"] and not ch["forms"][-1]:
                errs.append("index page after a fallback page: %s" % ln)
            vals = []
            for t in toks:
                if t == "-":
                    vals.append(None)
                elif form == "i":
                    vals.append(ch["dic"][int(t)])
                else:
                    vals.append(int(t))
            live = [v for v in vals if v is not None]
            if u != m - len(live):
                errs.append("null count: %s" % ln)
            if not live:
                if f[3] != "-" or f[4] != "-":
                    errs.append("all-null page with bounds: %s" % ln)
            else:
                lo, hi = min(live), max(live)
                if f[5] == "w":
                    lo, hi = -(-lo // g) * g, (hi // g) * g
                    if lo > hi:
                        errs.append("widened page whose rounding crosses: %s" % ln)
                if (str(lo), str(hi)) != (f[3], f[4]):
                    errs.append("recorded pair %s %s, values give %d %d: %s" % (f[3], f[4], lo, hi, ln))
            ch["forms"].append(form == "i")
            pages.append(vals)
            rows[ch["c"]] += m
        elif f[0] == "qry":
            close()
            ch = None
            qn = {"prd": 0, "prj": 0}
        elif f[0] == "prd":
            qn["prd"] += 1
        elif f[0] == "prj":
            qn["prj"] += len(f) - 1
        elif f[0] == "end":
            if not qn["prd"] or not qn["prj"]:
                errs.append("a query without a condition or a column")
        elif f[0] in ("up", "del"):
            close()
            ch = None
    close()
    for c in range(k):
        if rows[c] != n:
            errs.append("column %d covers %d rows, not %d" % (c, rows[c], n))
    return errs


def main():
    sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")


if __name__ == "__main__":
    main()
