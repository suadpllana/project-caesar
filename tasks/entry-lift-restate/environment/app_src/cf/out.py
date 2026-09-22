class Out:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def line(self, text):
        self.lines.append(text)
