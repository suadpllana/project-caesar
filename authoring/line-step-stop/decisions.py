"""The graded decisions, as rows for tools/onelinecheck.py.

    python ../../tools/onelinecheck.py line-step-stop

Replays sessions through the sealed model with its judgement instrumented and records, for
every decision, the integer quantities an engine can read at that moment and what was
chosen. The model and the reference print identical lines on every frozen session and on
every nonce population measured, so the model's decisions are the reference's. The
instrumented copy of `arrive` is checked against model.play on every session it samples: if
the two ever print different lines, this raises instead of reporting.

  arrival_stop     every arrival judged in the stepping frame (rules on leaving the scope,
                   instance entry and rows): does it end the command?
  hidden_at_stop   every stop: how many of the innermost frame's scopes are hidden
  break_count      every breakpoint: how many addresses it resolves to
  caller_line      every caller frame printed: the line its deepest scope shows
"""
import os
import random
import sys

# onelinecheck loads this file by path, so the bench beside it has to be put on the path here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab import forge, model  # noqa: E402

SEED = 5150
PER_FAMILY = 25
CMD = {"run": 0, "cont": 0, "step": 1, "next": 2, "finish": 3}
KIND = {"hit": 0, "step": 1, "done": 2}


class Probe(model.Session):
    def __init__(self, prog, tape, rec):
        super().__init__(prog, tape)
        self.rec = rec

    def arrive(self):
        """model.Session.arrive, recording each judgement it makes."""
        p = self.p
        while True:
            st = self.st
            addr = self.pc
            left = 0
            while st["scope"][0] == "i" and not p.holds(st["scope"], addr):
                st["scope"] = p.parent(st["scope"])
                left = 1
            ch = p.chain(addr)
            k = ch.index(st["scope"])
            below = [s for s in ch[k + 1:] if p.inl_lo[s[1]] == addr]
            ln = p.row_line[addr]
            row = {"row_line": 0 if ln is None else ln, "step_line": st["line"],
                   "stmt": int(bool(p.row_stmt[addr])), "row_start": int(bool(p.row_start[addr])),
                   "n_start": len(p.starting(addr)), "n_below": len(below),
                   "call_line": p.inl_call[below[0][1]] if below else 0,
                   "into": int(st["into"]), "left": left}
            if below:
                first = below[0]
                if p.inl_call[first[1]] == st["line"]:
                    if st["into"]:
                        self.rec["arrival_stop"].append((row, True))
                        self.hid = len(below) - 1
                        raise model.Stop("step")
                    self.rec["arrival_stop"].append((row, False))
                    self.over_instance(first)
                    continue
                self.rec["arrival_stop"].append((row, True))
                self.hid = len(below)
                raise model.Stop("step")
            if ln is None:
                self.rec["arrival_stop"].append((row, False))
                return
            if p.row_start[addr]:
                if p.row_stmt[addr] and ln != 0 and ln != st["line"]:
                    self.rec["arrival_stop"].append((row, True))
                    self.hid = 0
                    raise model.Stop("step")
                self.rec["arrival_stop"].append((row, False))
                return
            if ln != 0:
                st["line"] = ln
            self.rec["arrival_stop"].append((row, False))
            return


def replay(s, rec):
    """model.play, with the stop, breakpoint and frame decisions recorded."""
    prog = model.Program(s["image"])
    ses = Probe(prog, s["tape"], rec)
    out = []
    over = False
    for raw in s["cmds"]:
        w = raw.split()
        if not w:
            continue
        if w[0] == "break":
            line = int(w[1])
            text = ses.do_break(line)
            stmt = [a for a, ln, _ in prog.stmt_rows if ln == line]
            rows = [a for a in range(len(prog.code)) if prog.row_start[a] and prog.row_line[a] == line]
            rec["break_count"].append(({"stmt_rows": len(stmt), "rows": len(rows),
                                        "fns": len({prog.fn_of[a] for a in stmt})},
                                       len(text.split()) - 1))
            out.append(text)
            continue
        if over:
            out.append("exit")
            continue
        before = ses.hid
        try:
            {"run": ses.do_run, "cont": ses.do_cont, "finish": ses.do_finish,
             "step": lambda: ses.do_step(True), "next": lambda: ses.do_step(False)}[w[0]]()
        except model.Stop as e:
            rec["hidden_at_stop"].append(({"n_start": len(prog.starting(ses.pc)), "hid_before": before,
                                           "cmd": CMD[w[0]], "kind": KIND[e.kind]}, ses.hid))
            for ret, _ in ses.calls:
                a = ret - 1
                rec["caller_line"].append(({"line_at_call": prog.line(a), "line_at_ret": prog.line(ret),
                                            "n_inst": len(prog.holding[a])}, prog.line(a)))
            out.append(" ".join([e.kind, str(ses.pc)] + ses.frames()))
        except model.Ended:
            over = True
            out.append("exit")
    return out


def samples():
    rec = {"arrival_stop": [], "hidden_at_stop": [], "break_count": [], "caller_line": []}
    rng = random.Random(SEED)
    for fam in sorted(forge.FAMILIES):
        for _ in range(PER_FAMILY):
            s = forge.session(fam, rng)
            got = replay(s, rec)
            if got != model.play(s["image"], s["tape"], s["cmds"]):
                raise AssertionError("the instrumented replay drifted from model.play (%s)" % fam)
    return rec


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        labels = [y for _, y in rows]
        print("%-16s %5d rows, %d distinct labels" % (name, len(rows), len(set(map(str, labels)))))
