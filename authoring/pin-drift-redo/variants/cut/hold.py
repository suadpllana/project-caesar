OWED = 0
SET = 1


class Held:
    def __init__(self):
        self.form = {}

    def start(self, keys):
        for k in keys:
            self.form[k] = (OWED, k, 0)

    def at(self, k, taken):
        kind, one, two = self.form[k]
        if kind == SET:
            return one
        return taken.at(one) + two

    def put(self, k, n):
        self.form[k] = (SET, n, 0)

    def add(self, k, n):
        kind, one, two = self.form[k]
        if kind == SET:
            self.form[k] = (SET, one + n, 0)
        else:
            self.form[k] = (OWED, one, two + n)

    def copy(self, k, j):
        self.form[k] = self.form[j]

    def raw(self, k, j):
        self.form[k] = (OWED, j, 0)

    def stick(self, k, v):
        self.form[k] = (SET, v, 0)

    def save(self):
        return dict(self.form)

    def back(self, saved, keys):
        form = {}
        for k in keys:
            was = saved.get(k)
            form[k] = was if was is not None else (OWED, k, 0)
        self.form = form
