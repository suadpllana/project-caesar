import socket
import sys

from mach import Mach, load_code


def main():
    with open(sys.argv[1]) as f:
        code, entry = load_code(f.read())
    tape = [int(t) for t in sys.stdin.read().split()]
    sock = socket.socket(fileno=int(sys.argv[2]))
    rf = sock.makefile("rb")
    wf = sock.makefile("wb")
    m = Mach(code, entry, tape)
    while True:
        try:
            req = rf.readline()
        except OSError:
            break
        if not req:
            break
        kind = req[:1]
        if m.done:
            out = b"end"
        elif kind == b"p":
            out = b"%d" % m.pc
        elif kind == b"k":
            out = " ".join(str(r) for r in m.rets()).encode()
        elif kind == b"s":
            pc = m.one()
            out = b"end" if pc is None else b"%d" % pc
        elif kind == b"g":
            stops = {int(t) for t in req[1:].split()}
            pc = m.go(stops)
            out = b"end" if pc is None else b"%d" % pc
        else:
            out = b"?"
        try:
            wf.write(out + b"\n")
            wf.flush()
        except OSError:
            break


if __name__ == "__main__":
    main()
