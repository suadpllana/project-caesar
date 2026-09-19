class Meld:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = set()

    def first(self, tab, key):
        seat = (tab, key)
        if seat in self.seen:
            return False
        self.seen.add(seat)
        return True
