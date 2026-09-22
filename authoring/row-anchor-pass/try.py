"""Run one candidate program under the reference and under named readings; show where they part.

    python3 try.py 'cfg ...' 'g ...' ... -- reading [reading ...]
"""
import sys

import emit
import lab

argv = sys.argv[1:]
cut = argv.index("--") if "--" in argv else len(argv)
prog = argv[:cut]
names = argv[cut + 1:]
emit.MADE.clear()
for b in emit.READING_BUILDERS:
    b()
ref = lab.pane("solution")
want = ref(prog)
print("   " + " | ".join(prog))
for ln in want:
    print("   ref  " + ln)
for name in names:
    got = lab.tree(files=emit.BUILT[name])(prog)
    diff = [(a, b) for a, b in zip(want, got) if a != b]
    print("-- %s: %s" % (name, "SEPARATED" if got != want else "same"))
    for a, b in diff[:3]:
        print("   want " + a)
        print("   got  " + b)
