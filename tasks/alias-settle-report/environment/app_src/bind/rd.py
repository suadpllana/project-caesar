class Spec(object):
    def __init__(self):
        self.watch = []
        self.runs = {}
        self.tags = {}
        self.script = []


def parse(text):
    sp = Spec()
    body = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        bits = line.split()
        head = bits[0]
        if head == "go":
            body = True
            continue
        if not body:
            if head == "watch":
                sp.watch = [int(x) for x in bits[1:]]
            elif head == "run":
                sp.runs[bits[1]] = [int(x) for x in bits[2:]]
            elif head == "tag":
                sp.tags[bits[1]] = [int(x) for x in bits[2:]]
            continue
        if head == "post":
            sp.script.append(("post", bits[1], int(bits[2]), int(bits[3])))
        elif head == "tie":
            sp.script.append(("tie", bits[1], int(bits[2]), int(bits[3])))
        elif head == "bar":
            sp.script.append(("bar", bits[1], int(bits[2]), int(bits[3])))
        elif head == "shut":
            sp.script.append(("shut", bits[1], 0, 0))
    return sp
