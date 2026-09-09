"""Write the wrong-reading cheats for what a failed whole fired and pulled, as `cheat/*.sh`.

Each reading is the reference with one contiguous change, applied here by exact text
replacement that must fire exactly once, so a script cannot drift from the reading it
stands for. Two more are previous references verbatim: the one every first-round probe
agent wrote (re-parks under fill pace, counts admission under order pace), and the one
that kept firings but put a same-participant cancellation back and refused without
walking when nothing could fill.

The pipeline never executes `cheat/`; a reviewer reads it, and `readings.py` runs it.

    python authoring/repair-orderbook-engine/cheats.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
SOLN = TASK / "solution"
OLD = ROOT / "authoring" / "repair-orderbook-engine" / "old-reference"
OLD2 = ROOT / "authoring" / "repair-orderbook-engine" / "old-reference-2"
ENV = TASK / "environment" / "app_src" / "eng"
OUT = TASK / "cheat"

PARTS = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")

HEAD = "def admit(st, o, out):\n    frame = Frame(st)\n"

SAME = """    gone = []
    for order in frame.pulled:
        if frame.standing(order) and order not in gone:
            order.live = False
            gone.append(order)
"""

ANNOUNCE = """    out.row("pul", o.oid, "whole")
    for order in gone:
        out.row("pul", order.oid, "same")
    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
"""

RUN = """    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
"""

# name -> (rationale, [(module, old, new), ...]); each replacement must match exactly once.
READINGS = {
    # ------------------------------------------------------------ admission
    "whole-prechecks": (
        "decides order-pace admission by counting what rests, so a whole that would come "
        "up short never walks, fires nothing and pulls nothing.",
        [("hold.py", HEAD, HEAD.replace("    frame = Frame(st)\n",
                                        "    if st.pace != \"fill\" and room(st, o) < o.rem:\n"
                                        "        out.row(\"pul\", o.oid, \"whole\")\n"
                                        "        return\n    frame = Frame(st)\n"))]),
    "no-fill-shortcut": (
        "refuses without walking when the count says no fill is possible, so a walk that "
        "would only have pulled the participant's own orders never pulls them.",
        [("hold.py", HEAD, HEAD.replace("    frame = Frame(st)\n",
                                        "    if room(st, o) == 0:\n"
                                        "        out.row(\"pul\", o.oid, \"whole\")\n"
                                        "        return\n    frame = Frame(st)\n"))]),
    # ------------------------------------------------------------ firings
    "fired-reparked": (
        "puts what a failed whole fired back in the parked set with the rest of the state.",
        [("hold.py", ANNOUNCE + RUN, """    out.row("pul", o.oid, "whole")
    for order in gone:
        out.row("pul", order.oid, "same")
    a = st.arm
    for seq, order in frame.fired:
        a.by[order.oid] = order
        if order.side == "b":
            heapq.heappush(a.bq, (order.trp, seq, order))
        else:
            heapq.heappush(a.sq, (-order.trp, seq, order))
""")]),
    "fired-vanish": (
        "leaves what a failed whole fired out of the parked set and never runs it.",
        [("hold.py", ANNOUNCE + RUN, """    out.row("pul", o.oid, "whole")
    for order in gone:
        out.row("pul", order.oid, "same")
""")]),
    "fired-in-firing-order": (
        "runs what a failed whole fired in the order the discarded walk fired it, not in "
        "arrival order.",
        [("hold.py", "sorted(frame.fired, key=lambda x: x[0])", "frame.fired")]),
    "fired-inner-frame-lost": (
        "records a firing inside a whole the failed order ran in that inner frame only, so "
        "the enclosing failure does not run it again.",
        [("hold.py", """def fired(st, seq, order):
    for frame in frames(st):
        frame.fired.append((seq, order))
""", """def fired(st, seq, order):
    if frames(st):
        frames(st)[-1].fired.append((seq, order))
""")]),
    "fired-once": (
        "runs an order that fired inside a failed whole once, so an enclosing failure "
        "does not run it again.",
        [("hold.py", "class Tape:", "DONE = set()\n\n\nclass Tape:"),
         ("hold.py", "    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]\n",
          "    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])\n"
          "             if order not in DONE]\n    DONE.update(again)\n")]),
    "fired-after-siblings": (
        "defers what a failed whole fired to the waiting queue under fill pace, behind the "
        "siblings and the interrupted order.",
        [("hold.py", RUN, "    st.pend.extend(again)\n")]),
    "fired-keeps-fills": (
        "runs what a failed whole fired from what was left after the discarded execution, "
        "not from its full size.",
        [("hold.py", "    frame.restore(st)\n" + SAME,
          "    for _, order in frame.fired:\n        frame.orders.pop(order, None)\n"
          "    frame.restore(st)\n" + SAME)]),
    "trp-left-inside": (
        "discards the trp lines with the rest of the failed whole's output and never "
        "announces the firings again.",
        [("hold.py", "    for order in again:\n        out.row(\"trp\", order.oid)\n", "")]),
    "fired-before-cancel": (
        "announces what a failed whole fired before its cancellation line instead of after.",
        [("hold.py", ANNOUNCE, """    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
    out.row("pul", o.oid, "whole")
    for order in gone:
        out.row("pul", order.oid, "same")
""")]),
    "fired-run-at-once-in-order-pace": (
        "runs what a failed whole fired straight after its cancellation line under order "
        "pace instead of behind the waiting queue.",
        [("hold.py", RUN, """    from mkt.drv import submit
    for order in again:
        submit(st, order, out)
""")]),
    "fired-announced-one-at-a-time": (
        "announces each order a failed whole fired just before running it under fill pace, "
        "instead of announcing the whole batch first.",
        [("hold.py", "    for order in again:\n        out.row(\"trp\", order.oid)\n" + RUN,
          """    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            out.row("trp", order.oid)
            submit(st, order, out)
    else:
        for order in again:
            out.row("trp", order.oid)
        st.pend.extend(again)
""")]),
    # ------------------------------------------------------------ same-participant pulls
    "same-restored": (
        "puts a resting order pulled for same inside a failed whole back on the book with "
        "the rest of the state.",
        [("hold.py", SAME, "    gone = []\n")]),
    "same-not-reannounced": (
        "keeps a resting order pulled for same inside a failed whole off the book but never "
        "announces the cancellation again.",
        [("hold.py", "    for order in gone:\n        out.row(\"pul\", order.oid, \"same\")\n", "")]),
    "same-after-trp": (
        "announces the same cancellations after the firings instead of before them.",
        [("hold.py", ANNOUNCE, """    out.row("pul", o.oid, "whole")
    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
    for order in gone:
        out.row("pul", order.oid, "same")
""")]),
    "same-depth-one": (
        "records a same cancellation made inside a whole the failed order ran in that inner "
        "frame only, so the enclosing failure puts the order back.",
        [("hold.py", """def pulled(st, order):
    for frame in frames(st):
        frame.pulled.append(order)
""", """def pulled(st, order):
    if frames(st):
        frames(st)[-1].pulled.append(order)
""")]),
    "same-unscoped": (
        "keeps every same cancellation made inside a failed whole, including one of an order "
        "that only rested inside the discarded execution, which then never runs again.",
        [("hold.py", "        if frame.standing(order) and order not in gone:\n",
          "        if order not in gone:\n"),
         ("hold.py", "    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]\n",
          "    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])\n"
          "             if order not in gone]\n")]),
    "same-pulls-by-id": (
        "announces the same cancellations again in id order instead of the order they "
        "happened.",
        [("hold.py", "    for order in gone:\n        out.row(\"pul\", order.oid, \"same\")\n",
          "    for order in sorted(gone, key=lambda x: x.oid):\n"
          "        out.row(\"pul\", order.oid, \"same\")\n")]),
}

PREVIOUS = (
    ("whole-takes-back-firings", OLD,
     "the previous reference but one: decides admission by counting under order pace and "
     "re-parks what a failed whole fired under fill pace."),
    ("whole-restores-same-pulls", OLD2,
     "the previous reference: keeps what a failed whole fired, but puts a resting order it "
     "pulled for same back on the book, and refuses without walking when nothing could fill."),
)


def apply(name, edits):
    files = {p: (SOLN / p).read_text(encoding="utf-8") for p in PARTS if p != "hand.py"}
    files["hand.py"] = (ENV / "hand.py").read_text(encoding="utf-8")
    for module, old, new in edits:
        n = files[module].count(old)
        if n != 1:
            raise SystemExit("%s: replacement in %s matched %d times, not once" % (name, module, n))
        files[module] = files[module].replace(old, new)
    return files


def script(why, files):
    out = ["#!/bin/bash", "# " + why, "set -euo pipefail", 'APP="${APP:-/app}"',
           'mkdir -p "$APP/eng"']
    for p in PARTS:
        body = files[p]
        assert "STF_EOF" not in body
        out.append('cat > "$APP/eng/%s" <<\'STF_EOF\'' % p)
        out.append(body.rstrip("\n"))
        out.append("STF_EOF")
    return "\n".join(out) + "\n"


def write(name, text):
    path = OUT / ("cheat-%s.sh" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    path.chmod(0o755)
    return path


def main():
    OUT.mkdir(exist_ok=True)
    for name, (why, edits) in READINGS.items():
        write(name, script(why, apply(name, edits)))
    for name, src, why in PREVIOUS:
        files = {p: (src / p).read_text(encoding="utf-8") for p in PARTS if p != "hand.py"}
        files["hand.py"] = (ENV / "hand.py").read_text(encoding="utf-8")
        write(name, script(why, files))
    print("wrote %d cheats into %s" % (len(READINGS) + len(PREVIOUS), OUT))


if __name__ == "__main__":
    main()
