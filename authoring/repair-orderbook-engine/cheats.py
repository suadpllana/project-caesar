"""Write the wrong-reading cheats for what a failed whole fired, as runnable `cheat/*.sh`.

Each reading is the reference with one contiguous change, applied here by exact text
replacement that must fire exactly once, so a script cannot drift from the reading it
stands for. One more is the previous reference verbatim - the plan every probe agent
wrote, which re-parks under fill pace and decides admission by counting under order pace.

The pipeline never executes `cheat/`; a reviewer reads it, and `cheat_report.py` runs it.

    python authoring/repair-orderbook-engine/cheats.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
SOLN = TASK / "solution"
OLD = ROOT / "authoring" / "repair-orderbook-engine" / "old-reference"
ENV = TASK / "environment" / "app_src" / "eng"
OUT = TASK / "cheat"

PARTS = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")

TAIL = """    frame.restore(st)
    out.row("pul", o.oid, "whole")
    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
"""

# name -> (rationale, [(module, old, new), ...]); each replacement must match exactly once.
READINGS = {
    "whole-prechecks": (
        "decides order-pace admission by counting what rests, so a whole that would come "
        "up short never walks and fires nothing.",
        [("hold.py", "    if room(st, o) == 0:\n",
          "    if room(st, o) < o.rem and st.pace != \"fill\":\n")]),
    "fired-reparked": (
        "puts what a failed whole fired back in the parked set with the rest of the state.",
        [("hold.py", TAIL, """    frame.restore(st)
    a = st.arm
    for seq, order in frame.fired:
        a.by[order.oid] = order
        if order.side == "b":
            heapq.heappush(a.bq, (order.trp, seq, order))
        else:
            heapq.heappush(a.sq, (-order.trp, seq, order))
    out.row("pul", o.oid, "whole")
""")]),
    "fired-vanish": (
        "leaves what a failed whole fired out of the parked set and never runs it.",
        [("hold.py", TAIL, """    frame.restore(st)
    out.row("pul", o.oid, "whole")
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
        [("hold.py", """    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
""", "    st.pend.extend(again)\n")]),
    "fired-keeps-fills": (
        "runs what a failed whole fired from what was left after the discarded execution, "
        "not from its full size.",
        [("hold.py", "    frame.restore(st)\n    out.row(\"pul\", o.oid, \"whole\")\n    again",
          "    for _, order in frame.fired:\n        frame.orders.pop(order, None)\n"
          "    frame.restore(st)\n    out.row(\"pul\", o.oid, \"whole\")\n    again")]),
    "trp-left-inside": (
        "discards the trp lines with the rest of the failed whole's output and never "
        "announces the firings again.",
        [("hold.py", "    for order in again:\n        out.row(\"trp\", order.oid)\n", "")]),
    "fired-before-cancel": (
        "announces what a failed whole fired before its cancellation line instead of after.",
        [("hold.py", """    out.row("pul", o.oid, "whole")
    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
""", """    again = [order for _, order in sorted(frame.fired, key=lambda x: x[0])]
    for order in again:
        out.row("trp", order.oid)
    out.row("pul", o.oid, "whole")
""")]),
}

READINGS["fired-run-at-once-in-order-pace"] = (
    "runs what a failed whole fired straight after its cancellation line under order pace "
    "instead of behind the waiting queue.",
    [("hold.py", """    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
""", """    from mkt.drv import submit
    for order in again:
        submit(st, order, out)
""")])
READINGS["fired-announced-one-at-a-time"] = (
    "announces each order a failed whole fired just before running it under fill pace, "
    "instead of announcing the whole batch first.",
    [("hold.py", """    for order in again:
        out.row("trp", order.oid)
    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            submit(st, order, out)
    else:
        st.pend.extend(again)
""", """    if st.pace == "fill":
        from mkt.drv import submit
        for order in again:
            out.row("trp", order.oid)
            submit(st, order, out)
    else:
        for order in again:
            out.row("trp", order.oid)
        st.pend.extend(again)
""")])

PREVIOUS = ("whole-takes-back-firings",
            "the previous reference: decides admission by counting under order pace and "
            "re-parks what a failed whole fired under fill pace.")


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
    files = {p: (OLD / p).read_text(encoding="utf-8") for p in PARTS if p != "hand.py"}
    files["hand.py"] = (ENV / "hand.py").read_text(encoding="utf-8")
    write(PREVIOUS[0], script(PREVIOUS[1], files))
    print("wrote %d cheats into %s" % (len(READINGS) + 1, OUT))


if __name__ == "__main__":
    main()
