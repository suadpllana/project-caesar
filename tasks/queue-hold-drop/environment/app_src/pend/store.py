class Rec:
    def __init__(self, up, fld=None):
        self.up = up
        self.fld = dict(fld) if fld else {}

    def copy(self):
        return Rec(self.up, self.fld)


class Chg:
    def __init__(self, kind, a, b=None, c=None):
        self.kind = kind
        self.a = a
        self.b = b
        self.c = c
        self.sent = False


class St:
    def __init__(self):
        self.base = {}
        self.q = []
        self.sid = {}
        self.oid = set()
        self.nid = 0
        self.out = []
