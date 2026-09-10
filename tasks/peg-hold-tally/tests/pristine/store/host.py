from keep import live
from store.mark import Marks
from store.space import Space


class Host:
    def __init__(self):
        self.sp = Space()
        self.mk = Marks()
        self.ac = live.new()
        self.t = 0
