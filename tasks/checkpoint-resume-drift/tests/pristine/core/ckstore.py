from core.link import LinkError

CAP = 64
LIM = 1 << 40


class CkError(Exception):
    pass


class CkStore:
    def __init__(self, lk):
        self.lk = lk

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
        try:
            return self.lk.call("put", out)[0]
        except LinkError as exc:
            raise CkError(str(exc))

    def get(self):
        try:
            return list(self.lk.call("get", []))
        except LinkError as exc:
            raise CkError(str(exc))
