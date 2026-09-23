from .script import Bad


class Page:
    def __init__(self):
        self.par = {0: None}
        self.kid = {0: []}
        self.tag = {0: "page"}
        self.att = {0: {}}
        self.txt = {}

    def is_text(self, n):
        return n in self.txt

    def up(self, n):
        return self.par[n]

    def kids(self, n):
        return self.kid.get(n, ())

    def attr(self, n, name):
        return self.att[n].get(name)

    def text(self, n):
        return self.txt[n]

    def attached(self, n):
        while n is not None:
            if n == 0:
                return True
            n = self.par[n]
        return False

    def walk(self, n):
        todo = [n]
        while todo:
            x = todo.pop()
            yield x
            ks = self.kid.get(x)
            if ks:
                todo.extend(reversed(ks))

    def _live(self, n, what):
        if n not in self.par:
            raise Bad("%s %d does not exist" % (what, n))
        if not self.attached(n):
            raise Bad("%s %d is not on the page" % (what, n))

    def _box(self, n):
        self._live(n, "parent")
        if n in self.txt:
            raise Bad("text node %d cannot hold children" % n)

    def _put(self, n, p, pos):
        ks = self.kid[p]
        if pos is None:
            pos = len(ks)
        if pos > len(ks):
            raise Bad("position %d is past the end of %d" % (pos, p))
        ks.insert(pos, n)
        self.par[n] = p

    def apply(self, op):
        head = op[0]
        if head == "add":
            _, n, p, pos, kind, val = op
            if n in self.par:
                raise Bad("id %d is taken" % n)
            self._box(p)
            if kind == "el":
                self.kid[n] = []
                self.tag[n] = val
                self.att[n] = {}
            else:
                self.txt[n] = val
            self._put(n, p, pos)
            return ("add", n)
        if head == "move":
            _, n, p, pos = op
            self._live(n, "node")
            if n == 0:
                raise Bad("the page cannot move")
            self._box(p)
            x = p
            while x is not None:
                if x == n:
                    raise Bad("%d cannot move under itself" % n)
                x = self.par[x]
            old = self.par[n]
            self.kid[old].remove(n)
            self._put(n, p, pos)
            return ("move", n, old)
        if head == "drop":
            _, n = op
            self._live(n, "node")
            if n == 0:
                raise Bad("the page cannot be dropped")
            old = self.par[n]
            self.kid[old].remove(n)
            self.par[n] = None
            return ("drop", n, old)
        if head == "text":
            _, n, val = op
            self._live(n, "node")
            if n not in self.txt:
                raise Bad("%d is not text" % n)
            old = self.txt[n]
            self.txt[n] = val
            return ("text", n, old)
        _, n, name = op[:3]
        self._live(n, "element")
        if n == 0 or n in self.txt:
            raise Bad("%d cannot carry attributes" % n)
        old = self.att[n].get(name)
        if head == "set":
            self.att[n][name] = op[3]
            return ("set", n, name, old)
        self.att[n].pop(name, None)
        return ("unset", n, name, old)
