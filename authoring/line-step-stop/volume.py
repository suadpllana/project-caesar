"""Replay a session in the model and split its executed instructions by where they ran.

in_frame: executed while a step or next is judging rows in the stepping frame (including
          an inlined instance it steps over) - what an engine that single-steps its own
          frame pays for one round trip at a time.
elsewhere: executed inside calls being run to completion, or by cont and finish.
"""
from lab import model


def split(session):
    prog = model.Program(session["image"])
    s = model.Session(prog, session["tape"])
    counts = {"in_frame": 0, "elsewhere": 0}
    state = {"cmd": None}
    orig_exec = s.exec1

    def exec1():
        ctx = state["cmd"]
        if ctx in ("step", "next") and hasattr(s, "st") and s.depth() == s.st["d"]:
            counts["in_frame"] += 1
        else:
            counts["elsewhere"] += 1
        orig_exec()
    s.exec1 = exec1
    for raw in session["cmds"]:
        w = raw.split()
        if w[0] == "break":
            s.do_break(int(w[1]))
            continue
        state["cmd"] = w[0]
        try:
            {"run": s.do_run, "cont": s.do_cont, "finish": s.do_finish,
             "step": lambda: s.do_step(True), "next": lambda: s.do_step(False)}[w[0]]()
        except model.Stop:
            pass
        except model.Ended:
            break
    return counts
