class Store:
    def __init__(self):
        self.out = []
        self.by_node = {}
        self.by_job = {}
        self.pend = {}
        self.gone = set()
        self.n = 0

    def mark(self):
        self.n += 1
        return self.n


def boxof(node):
    cut = node.find(":")
    return node if cut < 0 else node[:cut]
