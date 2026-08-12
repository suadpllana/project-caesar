import json
import os

MAXF = 1 << 20


class LinkError(Exception):
    pass


class Link:
    def __init__(self, rfd, wfd):
        self.rfd = rfd
        self.wfd = wfd
        self.buf = b""

    def send(self, obj):
        data = (json.dumps(obj) + "\n").encode()
        while data:
            n = os.write(self.wfd, data)
            data = data[n:]

    def recv(self):
        while b"\n" not in self.buf:
            chunk = os.read(self.rfd, 65536)
            if not chunk:
                raise LinkError("the service closed the link")
            self.buf += chunk
            if len(self.buf) > MAXF:
                raise LinkError("frame too long")
        line, self.buf = self.buf.split(b"\n", 1)
        try:
            return json.loads(line.decode())
        except ValueError:
            raise LinkError("unreadable frame")

    def call(self, q, a):
        self.send({"q": q, "a": list(a)})
        m = self.recv()
        if not isinstance(m, dict):
            raise LinkError("unreadable reply")
        if "e" in m:
            raise LinkError(str(m["e"]))
        r = m.get("r")
        if not isinstance(r, list):
            raise LinkError("unreadable reply")
        return r
