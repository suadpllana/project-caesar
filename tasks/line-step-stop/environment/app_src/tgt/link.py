import os
import socket
import subprocess
import sys

SERVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serve.py")


class Link:
    def __init__(self, sock, proc=None):
        self.sock = sock
        self.proc = proc
        self.rf = sock.makefile("rb")
        self.wf = sock.makefile("wb")

    def _ask(self, req):
        self.wf.write(req)
        self.wf.flush()
        return self.rf.readline().strip()

    def pc(self):
        r = self._ask(b"p\n")
        return None if r == b"end" else int(r)

    def stack(self):
        r = self._ask(b"k\n")
        if r == b"end":
            return None
        return [int(t) for t in r.split()]

    def step(self):
        r = self._ask(b"s\n")
        return None if r == b"end" else int(r)

    def go(self, stops):
        r = self._ask(b"g " + " ".join(str(a) for a in stops).encode() + b"\n")
        return None if r == b"end" else int(r)

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.rf.close()
        self.wf.close()
        self.sock.close()
        if self.proc is not None:
            self.proc.wait()


def spawn(image, tape):
    ours, theirs = socket.socketpair()
    with open(tape) as src:
        proc = subprocess.Popen(
            [sys.executable, SERVE, image, str(theirs.fileno())],
            stdin=src,
            pass_fds=(theirs.fileno(),),
        )
    theirs.close()
    return Link(ours, proc)


def attach(fd):
    return Link(socket.socket(fileno=fd))
