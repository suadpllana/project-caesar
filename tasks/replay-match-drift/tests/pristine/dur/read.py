KIND = {
    "call": "call",
    "fire": "call",
    "spawn": "child",
    "nap": "timer",
}

AWAITS = ("call", "spawn", "nap")


class Prog(object):
    def __init__(self, body, log, feed):
        self.body = body
        self.log = log
        self.feed = feed


def parse(text):
    body = []
    log = []
    feed = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        part = line.split()
        head = part[0]
        if head == "b":
            body.append((part[1], part[2:]))
        elif head == "e":
            log.append((part[1], part[2:]))
        elif head == "r":
            feed.append(int(part[1]))
    return Prog(body, log, feed)
