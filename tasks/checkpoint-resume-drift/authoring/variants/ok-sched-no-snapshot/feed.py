class Feed:
    def __init__(self):
        self.cur = 0
        self.hd = None

    def draw(self, samp):
        sid = samp.pick(self.cur)
        self.cur += 1
        return sid

    def take(self):
        h = self.hd
        self.hd = None
        return h

    def hold(self, sid, bd):
        self.hd = (sid, bd)

    # Two fields, and the second one is the one that gets dropped.
    #
    # The cursor is obvious: it is where the sampler has got to, and without it the
    # stream restarts from the top of the epoch.
    #
    # The held item is the sample data.pack drew and had no room for.  It carries the
    # curriculum bound that was in force at the moment it was drawn, because data.pack
    # reads that bound once, when the item leaves the sampler, and then truncates to it
    # every time it tries to place the item - including at the next fill, and including
    # after a resume.  An item held across a save is therefore an item whose bound was
    # fixed under the schedule of the step that drew it.  Save the identifier alone and
    # the item comes back truncated to whatever the bound is after the load; if a
    # curriculum change or an amendment landed in between, that is a different row of
    # tokens, a different gradient, and a run that never rejoins the one it continues.
    def snap(self):
        if self.hd is None:
            return [self.cur, -1, -1]
        return [self.cur, self.hd[0], self.hd[1]]

    def rest(self, vec):
        if len(vec) == 3:
            self.cur = vec[0]
            self.hd = None if vec[1] < 0 else (vec[1], vec[2])
