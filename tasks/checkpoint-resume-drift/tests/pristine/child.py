import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.link import Link, LinkError


def work(lk, cx, m):
    import build
    from train import ckpt

    c = m.get("c")
    if c == "boot":
        return build.make(m.get("cfg"), lk), {}
    if cx is None:
        raise ValueError("no trainer is up")
    if c == "micro":
        for _ in range(int(m.get("n", 1))):
            cx.loop.micro()
        return cx, {}
    if c == "save":
        cx.ck.put(ckpt.pack_state(cx))
        return cx, {"step": cx.loop.step}
    if c == "load":
        ckpt.unpack_state(cx, cx.ck.get())
        return cx, {"step": cx.loop.step}
    if c == "amend":
        cx.amend(m.get("sched") or {}, m.get("top") or {})
        return cx, {}
    if c == "report":
        return cx, cx.report()
    raise ValueError("unknown command %r" % (c,))


def main(rfd, wfd):
    lk = Link(rfd, wfd)
    cx = None
    while True:
        try:
            m = lk.recv()
        except LinkError:
            return 0
        if not isinstance(m, dict) or m.get("c") == "stop":
            return 0
        try:
            cx, res = work(lk, cx, m)
        except LinkError:
            return 1
        except BaseException:
            try:
                lk.send({"x": traceback.format_exc()[-1200:]})
            except OSError:
                return 1
            continue
        try:
            lk.send({"ok": res})
        except OSError:
            return 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]), int(sys.argv[2])))
