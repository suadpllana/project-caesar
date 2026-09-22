from view.spec import Bad


class Box:
    def __init__(self, bid, own, fl):
        self.id = bid
        self.own = own
        self.pin = fl["pin"]
        self.shut = fl["shut"]
        self.lift = fl["lift"]
        self.live = fl["live"]
        self.kids = []
        self.par = None
        self.gone = False


class View:
    def __init__(self, prog):
        self.vh = prog.vh
        self.kids = []
        self.box = {}
        self.log = []
        for bid, par, own, fl in prog.decl:
            b = Box(bid, own, fl)
            self.under(par).append(b)
            b.par = None if par == "-" else self.box[par]
            self.box[bid] = b
        self.s = prog.at

    def under(self, par):
        if par == "-" or par is None:
            return self.kids
        if isinstance(par, Box):
            return par.kids
        return self.find(par).kids

    def find(self, bid):
        b = self.box.get(bid)
        if b is None:
            raise Bad("no box %s in the tree" % bid)
        return b

    def apply(self, op):
        kind, bid, arg = op
        if kind == "to":
            self.log.append(("to", None, arg))
            return
        if kind == "add":
            par, at, own, fl = arg
            row = self.under(par)
            if at > len(row):
                raise Bad("add %s: index %d past the end" % (bid, at))
            b = Box(bid, own, fl)
            b.par = None if par == "-" else self.box[par]
            row.insert(at, b)
            self.box[bid] = b
            self.log.append(("add", b, at))
            return
        b = self.find(bid)
        if kind == "size":
            b.own = arg
        elif kind == "drop":
            self.under(b.par).remove(b)
            todo = [b]
            while todo:
                x = todo.pop()
                x.gone = True
                del self.box[x.id]
                todo.extend(x.kids)
        elif kind == "shut":
            b.shut = True
        elif kind == "open":
            b.shut = False
        elif kind == "pin":
            b.pin = arg
        elif kind == "unpin":
            b.pin = None
        elif kind == "lift":
            b.lift = True
        elif kind == "sink":
            b.lift = False
        self.log.append((kind, b, arg))
