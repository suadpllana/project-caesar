class Log:
    """One undo journal for the transaction; a savepoint is its length when made. Every change
    - a row, a ledger entry, a mode - is noted as the record that undoes it, so nothing is ever
    copied and a client that wraps each statement in a savepoint stays linear."""

    def __init__(self):
        self.recs = []
        self.marks = []

    def reset(self):
        self.recs = []
        self.marks = []

    def note(self, rec):
        self.recs.append(rec)

    def here(self):
        return len(self.recs)

    def since(self, n):
        return self.recs[n:]

    def unwind(self, n, undo):
        while len(self.recs) > n:
            undo(self.recs.pop())

    def mark(self, name):
        self.marks.append((name, len(self.recs)))

    def find(self, name):
        for i in range(len(self.marks) - 1, -1, -1):
            if self.marks[i][0] == name:
                return i
        return None

    def release(self, name):
        """Drop the latest savepoint with this name and every savepoint made after it."""
        i = self.find(name)
        if i is None:
            return False
        del self.marks[i:]
        return True

    def back_to(self, name):
        """Where the latest savepoint with this name began; it stays, later ones are dropped."""
        i = self.find(name)
        if i is None:
            return None
        del self.marks[i + 1:]
        return self.marks[i][1]
