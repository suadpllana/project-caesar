CAP = 64
LIM = 1 << 40


class CkError(Exception):
    pass


class CkStore:
    def __init__(self):
        self.blob = None

    def put(self, vec):
        if not isinstance(vec, (list, tuple)):
            raise CkError("checkpoint payload is not a vector")
        out = []
        for x in vec:
            if isinstance(x, bool) or not isinstance(x, int):
                raise CkError("checkpoint payload holds a non integer slot")
            if x < -LIM or x > LIM:
                raise CkError("checkpoint slot out of range")
            out.append(x)
        if len(out) > CAP:
            raise CkError("checkpoint payload is %d slots, the channel holds %d" % (len(out), CAP))
        self.blob = out
        return len(out)

    def get(self):
        if self.blob is None:
            raise CkError("no checkpoint in the channel")
        return list(self.blob)
