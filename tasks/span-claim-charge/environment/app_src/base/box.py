from store import dev, hold, item, line, tally


class Store:
    def __init__(self, blocks):
        self.blocks = blocks
        dev.setup(self)
        hold.setup(self)
        tally.setup(self)
        line.setup(self)
        item.setup(self)
