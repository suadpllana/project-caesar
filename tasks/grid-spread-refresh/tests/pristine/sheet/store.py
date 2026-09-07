BLK = "#BLK"


class St:
    def __init__(self, nr):
        self.nr = nr
        self.ow = {}
        self.dv = {}
        self.tch = {}

    def own(self, ad):
        return ad in self.ow

    def node(self, ad):
        e = self.ow.get(ad)
        if e is None or e[0] != "f":
            return None
        return e[1]

    def val(self, ad):
        return self.dv.get(ad)

    def show(self, ad, v):
        if ad not in self.tch:
            self.tch[ad] = self.dv.get(ad)
        if v is None:
            self.dv.pop(ad, None)
        else:
            self.dv[ad] = v


def sho(v):
    if v is None:
        return "-"
    return str(v)
