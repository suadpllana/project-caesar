class Sp:
    def __init__(self, heap):
        self.heap = heap
        self.marks = []

    def clear(self):
        self.marks = []

    def mark(self, name):
        self.marks.append((name, self.heap.snap()))

    def find(self, name):
        for i in range(len(self.marks) - 1, -1, -1):
            if self.marks[i][0] == name:
                return i
        return None

    def back(self, name):
        i = self.find(name)
        if i is None:
            return False
        self.heap.load(self.marks[i][1])
        del self.marks[i + 1:]
        return True

    def drop(self, name):
        i = self.find(name)
        if i is None:
            return False
        del self.marks[i]
        return True
