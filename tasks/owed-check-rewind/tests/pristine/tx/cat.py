class Table:
    def __init__(self, name, cols):
        self.name = name
        self.key = cols[0]
        self.cols = list(cols[1:])
        self.pos = {c: i for i, c in enumerate(self.cols)}


class Con:
    kind = None

    def __init__(self, idx, name, table, col, deferrable, deferred):
        self.idx = idx
        self.name = name
        self.table = table
        self.col = col
        self.deferrable = deferrable
        self.deferred = deferred


class Check(Con):
    kind = "check"

    def __init__(self, idx, name, table, col, test, floor, deferrable, deferred):
        super().__init__(idx, name, table, col, deferrable, deferred)
        self.test = test
        self.floor = floor


class Fk(Con):
    kind = "fk"

    def __init__(self, idx, name, table, col, parent, action, deferrable, deferred):
        super().__init__(idx, name, table, col, deferrable, deferred)
        self.parent = parent
        self.action = action


class Cat:
    def __init__(self):
        self.tables = {}
        self.cons = []
        self.by = {}

    def add_table(self, name, cols):
        self.tables[name] = Table(name, cols)

    def add(self, con):
        self.cons.append(con)
        self.by[con.name] = con

    def con(self, name):
        return self.by[name]

    def checks_on(self, table):
        return [c for c in self.cons if c.kind == "check" and c.table == table]

    def fks_from(self, table):
        return [c for c in self.cons if c.kind == "fk" and c.table == table]

    def fks_into(self, table):
        return [c for c in self.cons if c.kind == "fk" and c.parent == table]
