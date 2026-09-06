class St:
    def __init__(self, fl, ss):
        self.fl = fl
        self.ss = ss
        self.t = b""
        self.n = 0
        self.r = 0

    def add(self, b):
        self.n += 1
        if b:
            self.t += b
