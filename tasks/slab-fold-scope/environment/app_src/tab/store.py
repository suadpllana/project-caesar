class Tab:
    def __init__(self):
        self.head = 0
        self.next = 1
        self.props = {}
        self.buck = {}
        self.out = []

    def mint(self):
        sid = self.next
        self.next += 1
        return sid
