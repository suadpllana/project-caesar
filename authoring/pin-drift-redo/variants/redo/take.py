NAMED = {
    "rd": (2,),
    "put": (2,),
    "add": (2,),
    "cpy": (2, 3),
    "raw": (2, 3),
    "chk": (2,),
    "lim": (2,),
}


def names(op):
    if op[0] == "bmp":
        return tuple(range(op[2], op[3]))
    where = NAMED.get(op[0])
    if where is None:
        return ()
    return tuple(op[i] for i in where)


class Taken:
    def __init__(self):
        self.num = {}

    def see(self, store, keys):
        fresh = []
        moved = False
        for k in keys:
            standing = store.at(k)
            if k not in self.num:
                self.num[k] = standing
                fresh.append(k)
            elif self.num[k] != standing:
                self.num[k] = standing
                moved = True
        return fresh, moved

    def again(self, store):
        for k in self.num:
            standing = store.at(k)
            if self.num[k] != standing:
                self.num[k] = standing

    def at(self, k):
        return self.num[k]

    def keys(self):
        return list(self.num)
