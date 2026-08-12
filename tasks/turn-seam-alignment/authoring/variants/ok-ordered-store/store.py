import collections


class Store:
    def __init__(self, cap):
        self.cap = int(cap)
        self.d = collections.OrderedDict()

    def get(self, k):
        e = self.d.get(k)
        if e is None:
            return None
        self.d.move_to_end(k)
        return e

    def put(self, k, text, ids):
        self.d[k] = (text, list(ids))
        self.d.move_to_end(k)
        while len(self.d) > self.cap:
            self.d.popitem(last=False)

    def drop(self, k):
        self.d.pop(k, None)
