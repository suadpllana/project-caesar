class Know:
    def __init__(self):
        self.said = {}

    def fresh(self, r, text):
        return self.said.get(r) != text

    def mark(self, r, text):
        self.said[r] = text
