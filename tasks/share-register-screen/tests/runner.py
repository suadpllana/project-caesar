"""The only place a submission's code runs.

It drives the rebuilt screen over two sets of registers and writes one report. It never
decides anything: the report is evidence, and tests/test_outputs.py is what judges it,
afterwards, as root, without importing a line of it.

Three things beyond the records are recorded, because agent code shares this interpreter
with the instrumentation:

  * the frozen entry points as they actually stood, at import and again when the last
    register was done, against which the grader puts digests it derives by compiling the
    pristine sources;
  * how many times the interpreter itself entered the seat allocation and the register
    reader, kept in a closure this module owns rather than anywhere the tree can reach,
    and whether the instrumentation was still armed at the end;
  * the run nonce, which is made from /dev/urandom by test.sh after the agent has
    finished, so a report written before the run cannot pass.

None of that is a proof. What it buys is that every way around it is a separate, visible
act rather than a quiet one.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, "/tests")

import cases  # noqa: E402
import gen  # noqa: E402
import mark  # noqa: E402

TOOL = 4
WATCH = ("elect", "load", "stakes")


def _counter():
    tally = {k: 0 for k in WATCH}
    return tally


def _arm(tally, targets):
    """Count entries into the frozen entry points, in a closure the tree cannot reach."""
    mon = getattr(sys, "monitoring", None)
    if mon is not None and hasattr(mon, "use_tool_id"):
        codes = {}
        for label, fn in targets:
            codes[fn.__code__] = label
        mon.use_tool_id(TOOL, "srs")

        def hit(code, offset):
            label = codes.get(code)
            if label is not None:
                tally[label] += 1
            return mon.DISABLE if label is None else None

        mon.register_callback(TOOL, mon.events.PY_START, hit)
        for code in codes:
            mon.set_local_events(TOOL, code, mon.events.PY_START)

        def down():
            live = False
            try:
                live = mon.get_tool(TOOL) == "srs"
            except (ValueError, RuntimeError):
                live = False
            try:
                mon.free_tool_id(TOOL)
            except (ValueError, RuntimeError):
                pass
            return live
        return down, "monitoring"

    names = {}
    for label, fn in targets:
        names[fn.__code__] = label

    def hook(frame, event, arg):
        if event == "call":
            label = names.get(frame.f_code)
            if label is not None:
                tally[label] += 1
        return None

    sys.setprofile(hook)

    def down():
        live = sys.getprofile() is hook
        sys.setprofile(None)
        return live
    return down, "profile"


def main(argv):
    nonce = os.environ.get("SRS_NONCE", "")
    count = int(os.environ.get("SRS_COUNT", "300"))
    fd = int(os.environ.get("SRS_FD", "3"))
    app = os.environ.get("APPDIR", "/work/app")
    sys.path.insert(0, app)

    if os.environ.get("SRS_REQUIRE_MONITORING") == "1" and not hasattr(sys, "monitoring"):
        raise SystemExit("interpreter without sys.monitoring")

    from reg import book, poll, run, site

    targets = (("elect", poll.elect), ("load", book.load), ("stakes", site.Site.stakes))
    at_import = mark.live(
        [("reg.poll.elect", poll.elect), ("reg.book.load", book.load),
         ("reg.site.Site.stakes", site.Site.stakes),
         ("reg.site.Site.voter", site.Site.voter), ("reg.run.drive", run.drive)])

    tally = _counter()
    down, how = _arm(tally, targets)

    work = list(cases.CASES) + gen.batch(nonce, count)
    rows = {}
    for name, text in work:
        try:
            rows[name] = run.drive(book.load(text))
        except Exception as exc:  # a submission that raises fails that register, not the run
            rows[name] = {"raised": "%s: %s" % (type(exc).__name__, exc)}

    at_end = mark.live(
        [("reg.poll.elect", poll.elect), ("reg.book.load", book.load),
         ("reg.site.Site.stakes", site.Site.stakes),
         ("reg.site.Site.voter", site.Site.voter), ("reg.run.drive", run.drive)])
    armed = down()

    report = {
        "nonce": nonce,
        "count": count,
        "names": [n for n, _ in work],
        "rows": rows,
        "marks": {"import": at_import, "end": at_end},
        "tally": tally,
        "armed": bool(armed),
        "how": how,
    }
    with os.fdopen(fd, "w") as sink:
        sink.write(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
