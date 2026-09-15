from mix import book


class Hold:

    def __init__(self):
        self.seed = 0
        self.book = book.Book()
        self.epoch = {}
        self.cur = {}
        self.cnt = {}
        self.step = 0
        self.ranks = 0
        self.micro = 0
        self.accum = 0
        self.mark = None
        self.out = []
