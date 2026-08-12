def _pick(tab, step):
    v = tab[0][1]
    for k, x in tab:
        if step >= k:
            v = x
    return v


class Sched:
    def __init__(self, cfg):
        self.cfg = cfg
        self.at_ = -1
        self.val = None

    def _calc(self, step):
        s = self.cfg["sched"]
        w = s["warm"]
        b = s["base"]
        if step < w:
            lr = (b * (step + 1)) // w
        else:
            lr = b - 3 * (step - w)
            if lr < 8:
                lr = 8
        return [lr, _pick(s["bounds"], step), _pick(s["window"], step), _pick(s["ema"], step)]

    def at(self, step):
        if self.at_ != step or self.val is None:
            self.val = self._calc(step)
            self.at_ = step
        return self.val

    def clear(self):
        self.at_ = -1
        self.val = None

    def lr(self, step):
        return self.at(step)[0]

    def bound(self, step):
        return self.at(step)[1]

    def wsize(self, step):
        return self.at(step)[2]

    def eshift(self, step):
        return self.at(step)[3]

    def snap(self):
        if self.val is None:
            return [-1, 0, 0, 0, 0]
        return [self.at_] + list(self.val)

    def rest(self, vec):
        if len(vec) >= 5 and vec[0] >= 0:
            self.at_ = vec[0]
            self.val = list(vec[1:5])
