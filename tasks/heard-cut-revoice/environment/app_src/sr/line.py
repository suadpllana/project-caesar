from collections import deque


class Line:
    def __init__(self):
        self.q = deque()

    def push(self, cls, text):
        self.q.append((cls, text))

    def flush(self):
        self.q.clear()

    def pop(self):
        return self.q.popleft() if self.q else None
