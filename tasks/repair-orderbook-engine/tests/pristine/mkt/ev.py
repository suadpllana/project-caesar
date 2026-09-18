class Emit:
    def __init__(self, sink):
        self.sink = sink

    def row(self, *cells):
        self.sink(tuple(cells))
