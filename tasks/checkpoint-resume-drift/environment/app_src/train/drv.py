import copy
import json
import os
import select
import signal
import subprocess
import sys
import time

from core.svc import Svc, SvcError

MAXF = 1 << 20
WAIT = 180.0


class RunError(Exception):
    pass


def appdir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.environ.get("APPDIR") or os.path.dirname(here)


def wrap():
    u = os.environ.get("LIFE_UID")
    if not u or not u.isdigit() or os.geteuid() != 0:
        return []
    return ["setpriv", "--reuid", u, "--regid", u, "--clear-groups"]


def reap():
    u = os.environ.get("LIFE_UID")
    if not u or not u.isdigit() or os.geteuid() != 0:
        return
    uid = int(u)
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            if os.stat("/proc/%d" % pid).st_uid == uid:
                os.kill(pid, signal.SIGKILL)
        except OSError:
            continue


class Life:
    def __init__(self, sv):
        self.sv = sv
        self.buf = b""
        r1, w1 = os.pipe()
        r2, w2 = os.pipe()
        app = appdir()
        env = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONPATH": app,
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": "/nonexistent",
            "TMPDIR": "/nonexistent",
            "LC_ALL": "C",
        }
        self.proc = subprocess.Popen(
            wrap() + [sys.executable, os.path.join(app, "child.py"), str(r1), str(w2)],
            cwd=app, env=env, pass_fds=(r1, w2), close_fds=True,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            start_new_session=True)
        os.close(r1)
        os.close(w2)
        self.rfd = r2
        self.wfd = w1
        self.pid = self.proc.pid

    def send(self, obj):
        data = (json.dumps(obj) + "\n").encode()
        while data:
            n = os.write(self.wfd, data)
            data = data[n:]

    def recv(self):
        end = time.time() + WAIT
        while b"\n" not in self.buf:
            left = end - time.time()
            if left <= 0:
                raise RunError("the trainer stopped answering")
            rd = select.select([self.rfd], [], [], left)[0]
            if not rd:
                continue
            chunk = os.read(self.rfd, 65536)
            if not chunk:
                raise RunError("the trainer went away")
            self.buf += chunk
            if len(self.buf) > MAXF:
                raise RunError("the trainer sent a frame longer than the link carries")
        line, self.buf = self.buf.split(b"\n", 1)
        try:
            m = json.loads(line.decode())
        except (ValueError, UnicodeDecodeError):
            raise RunError("the trainer sent an unreadable frame")
        if not isinstance(m, dict):
            raise RunError("the trainer sent an unreadable frame")
        return m

    def cmd(self, obj):
        self.send(obj)
        while True:
            m = self.recv()
            if "q" in m:
                try:
                    r = self.sv.handle(m.get("q"), m.get("a"))
                except SvcError as exc:
                    self.send({"e": str(exc)})
                    continue
                self.send({"r": r})
                continue
            if "ok" in m:
                return m["ok"] if isinstance(m["ok"], dict) else {}
            if "x" in m:
                raise RunError(str(m["x"])[-1200:])
            raise RunError("the trainer sent an unreadable frame")

    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            self.proc.wait(timeout=30)
        except Exception:
            pass
        for fd in (self.rfd, self.wfd):
            try:
                os.close(fd)
            except OSError:
                pass
        reap()


def play(cfg, ops, dseed):
    sv = Svc(copy.deepcopy(cfg), dseed)
    state = {"life": None}

    def start():
        life = Life(sv)
        sv.lives.append(life.pid)
        state["life"] = life
        life.cmd({"c": "boot", "cfg": sv.cfg})

    def stop():
        life = state["life"]
        if life is not None:
            state["life"] = None
            life.kill()

    def up():
        if state["life"] is None:
            raise RunError("no trainer is up")
        return state["life"]

    try:
        start()
        for op in ops:
            o = op.get("op")
            if o == "micro":
                up().cmd({"c": "micro", "n": int(op.get("n", 1))})
            elif o == "save":
                sv.ctr["saves"] += 1
                sv.note("S:%d" % sv.step_of(up().cmd({"c": "save"})))
            elif o == "kill":
                stop()
                sv.note("K")
            elif o == "load":
                stop()
                sv.ctr["loads"] += 1
                start()
                sv.note("L:%d" % sv.step_of(up().cmd({"c": "load"})))
            elif o == "amend":
                sched = op.get("sched") or {}
                top = op.get("top") or {}
                sv.amend(sched, top)
                if state["life"] is not None:
                    state["life"].cmd({"c": "amend", "sched": sched, "top": top})
                sv.note("A")
            else:
                raise RunError("unknown op %r" % (o,))
        return sv.state(up().cmd({"c": "report"}))
    except SvcError as exc:
        raise RunError(str(exc))
    finally:
        stop()
