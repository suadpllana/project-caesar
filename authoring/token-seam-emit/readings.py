"""The wrong readings, as solvers rather than as prose.

Each entry is a complete set of the four editable modules implementing one reading of the
brief, reachable from the tree the agent is given. Reachability is the point: an earlier
ablation of this task measured variants that broke `sm.py`, which ships correct, and
concluded the character seam was the dominant failure. No agent produces that variant, so
the number meant nothing.

`core` marks the readings that turn on the floor regime — the one place where the release
point stops being a function of the current step. The others are readings a competent
solver can hold while implementing its first plan faithfully.

Usage:
    python3 authoring/token-seam-emit/readings.py <task-dir> [count]
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SM_OK = """def dl(c):
    if c < 0xC0:
        return 1
    if c < 0xE0:
        return 2
    if c < 0xF0:
        return 3
    return 4


def back(s, i):
    c = getattr(s, "cb", None)
    if c is None:
        c = [0]
        s.cb = c
    t = s.t
    p = c[0] if c[0] <= i else 0
    while p < i:
        w = dl(t[p])
        if p + w > i:
            break
        p += w
    if p > c[0]:
        c[0] = p
    return p
"""

PIN_OK = """def first(s):
    c = getattr(s, "hf", None)
    if c is None:
        c = [-1, 0]
        s.hf = c
    t = s.t
    n = len(t)
    m = 0
    for x in s.ss:
        if len(x) > m:
            m = len(x)
    j = c[1] - m + 1
    if j < 0:
        j = 0
    b = c[0]
    for x in s.ss:
        if not x:
            continue
        k = t.find(x, j)
        if k >= 0 and (b < 0 or k < b):
            b = k
    c[1] = n
    c[0] = b
    return b


def pin(s):
    t = s.t
    n = len(t)
    b = n
    for x in s.ss:
        w = len(x) - 1
        if w > n:
            w = n
        while w > 0:
            if x[:w] == t[n - w:]:
                if n - w < b:
                    b = n - w
                break
            w -= 1
    return b
"""

PIN_WINDOW = PIN_OK[:PIN_OK.index("def pin(s):")] + """def pin(s):
    n = len(s.t)
    m = 0
    for x in s.ss:
        if len(x) > m:
            m = len(x)
    if m <= 1:
        return n
    b = n - m + 1
    return b if b > 0 else 0
"""

REL_OK = """from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
"""

# Below the floor nothing is checked at all, so everything is released. The natural reading
# of a floor that suppresses stop strings.
REL_BLIND = """from strm import hb, sm


def point(s):
    if s.n < s.fl:
        return sm.back(s, len(s.t)), False, ""
    f = hb.first(s)
    if f >= 0:
        return f, True, "stop"
    p = hb.pin(s)
    return sm.back(s, p), False, ""
"""

# Partials are held, but a complete occurrence standing below the floor does not pin the
# release point. The subtle half of the same mistake.
REL_NOPIN = """from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    p = hb.pin(s)
    return sm.back(s, p), False, ""
"""

# The floor is ignored: an occurrence terminates the request wherever it completes.
REL_NOFLOOR = """from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
"""

# The held tail is flushed on a stop finish instead of dropped.
REL_FLUSH = """from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return len(s.t), True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
"""

# Truncation at the end of the occurrence rather than at its start.
REL_AFTER = """from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        w = 0
        for x in s.ss:
            if x and s.t[f:f + len(x)] == x and len(x) > w:
                w = len(x)
        return f + w, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
"""

FIN_OK = """from strm import sm
from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS and s.n >= s.fl:
        return sm.back(s, len(s.t)), True, "eos"
    if last:
        return sm.back(s, len(s.t)), True, "length"
    return i, False, ""
"""

FIN_EOS = """from strm import sm
from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS:
        return sm.back(s, len(s.t)), True, "eos"
    if last:
        return sm.back(s, len(s.t)), True, "length"
    return i, False, ""
"""

FIN_RAW = """from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS and s.n >= s.fl:
        return len(s.t), True, "eos"
    if last:
        return len(s.t), True, "length"
    return i, False, ""
"""

READINGS = {
    "blind-below-floor": (True, REL_BLIND, PIN_OK, FIN_OK,
                          "below the floor nothing is checked, so nothing is held"),
    "no-pin": (True, REL_NOPIN, PIN_OK, FIN_OK,
               "partials are held but a standing occurrence does not pin the release point"),
    "floor-ignored": (True, REL_NOFLOOR, PIN_OK, FIN_OK,
                      "an occurrence terminates wherever it completes"),
    "eos-below-floor": (True, REL_OK, PIN_OK, FIN_EOS,
                        "a suppressed end-of-stream piece finishes the request anyway"),
    "fixed-window": (False, REL_OK, PIN_WINDOW, FIN_OK,
                     "hold back the longest stop minus one, always"),
    "flush-on-stop": (False, REL_FLUSH, PIN_OK, FIN_OK,
                      "the held tail is sent when the occurrence is found"),
    "cut-after-stop": (False, REL_AFTER, PIN_OK, FIN_OK,
                       "the occurrence itself is included in the output"),
    "raw-flush": (False, REL_OK, PIN_OK, FIN_RAW,
                  "the final flush ignores the trailing incomplete character"),
}

ENUM = r'''
import os, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import cases, gen, oracle
from strm import req
from tok import vocab
import tempfile
work = tempfile.mkdtemp()
first = 'none'
for nm, spec in cases.CASES:
    key = 'h_' + nm
    p = os.path.join(work, key + '.txt')
    gen.write(spec, p)
    want = oracle.rows(key, spec, vocab.PC, vocab.SP, vocab.EOS)
    got = []
    try:
        req.run(key, p, got)
    except Exception:
        got = []
    if got != want:
        first = nm
        break
print(first)
'''

PROBE = r'''
import sys, os
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import gen, oracle
from strm import req
from tok import vocab
bad = 0
for name, spec in gen.make(%r, %d):
    p = os.path.join(%r, name + ".txt")
    gen.write(spec, p)
    want = oracle.rows(name, spec, vocab.PC, vocab.SP, vocab.EOS)
    got = []
    try:
        req.run(name, p, got)
    except Exception:
        got = []
    if want != got:
        bad += 1
print(bad)
'''


def build(task, work, name):
    """A tree with the shipped frozen files and one reading's editable four."""
    core, rel, hb, fin, _ = READINGS[name]
    tree = os.path.join(work, "r_" + name)
    shutil.rmtree(tree, ignore_errors=True)
    shutil.copytree(os.path.join(task, "environment", "app_src"), tree)
    shutil.copy(os.path.join(task, "solution", "sm.py"), os.path.join(tree, "strm", "sm.py"))
    for fn, body in (("rel.py", rel), ("hb.py", hb), ("fin.py", fin)):
        with open(os.path.join(tree, "strm", fn), "w", encoding="ascii") as fh:
            fh.write(body)
    return tree


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    task = argv[0]
    count = int(argv[1]) if len(argv) > 1 else 400
    work = tempfile.mkdtemp(prefix="tse-readings-")
    cases = os.path.join(work, "cases")
    os.makedirs(cases, exist_ok=True)
    tests = os.path.join(task, "tests")

    print("%-20s %5s %9s %10s  %s"
          % ("reading", "core", "req-fail", "enumerated", "what it holds"))
    seen = {}
    enum = {}
    for name in sorted(READINGS):
        core = READINGS[name][0]
        tree = build(task, work, name)
        src = PROBE % (tree, tests, "nonce-a", count, cases)
        r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True)
        if r.returncode != 0:
            print("%-20s ERROR %s" % (name, r.stderr.strip().splitlines()[-1:]))
            return 1
        bad = int(r.stdout.strip())
        seen[name] = bad
        # readingcheck's question, asked directly: does a NAMED case fail this reading, or
        # does only the generated space catch it? A reading caught only by generated
        # requests reports as "6 of 300 wrong" instead of naming the rule that broke.
        e = subprocess.run([sys.executable, "-c", ENUM % (tree, tests)],
                           capture_output=True, text=True)
        hit = e.stdout.strip().splitlines()[-1] if e.returncode == 0 else "ERROR"
        enum[name] = hit
        print("%-20s %5s %8.1f%% %10s  %s"
              % (name, "yes" if core else "-", 100.0 * bad / count, hit,
                 READINGS[name][4]))

    worst_core = max(v for k, v in seen.items() if READINGS[k][0])
    zero = [k for k, v in seen.items() if v == 0]
    blind = [k for k, v in enum.items() if v in ("none", "ERROR")]
    print()
    print("every reading separated: %s" % ("no: " + ", ".join(zero) if zero else "yes"))
    print("every reading named by an enumerated case: %s"
          % ("no, BLIND: " + ", ".join(blind) if blind else "yes"))
    print("hardest core reading fails %.1f%% of requests" % (100.0 * worst_core / count))
    return 1 if (zero or blind) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
