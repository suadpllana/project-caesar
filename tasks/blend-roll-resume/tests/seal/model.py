"""The sealed model: what every graded script is supposed to print.

Written apart from the reference and from a different reading of the same arithmetic, so the
two agreeing is evidence about the contract rather than about one author's algebra.

The reference settles a segment by binary search over the grid of the weights' lowest common
multiple, where every candidate virtual time lies, and finds a departure from a closed form.
This file never builds that grid. It asks each source its own question instead - "how many
draws have you had once the segment has taken `seen` of them?" - and answers it by bisecting
that source's own draw number against `_spot`, which is the only relation the two files share
and is a direct statement of the rule. A departure is then found by bisecting the distance to
advance until the source's count reaches its last permitted sample, rather than by solving for
it. Both are O(log) in the distance and neither is the other's method.

The permutation is a copy of the shipped one rather than an import: nothing here reads a file
the submission could have changed.

The rules, and where each is applied:

  1  a draw goes to the live source with the smallest counter over weight, the earlier
     declared source taking a tie                                      `_who`, `_spot`
  2  every live source's counter goes back to 0 when the blend changes  `_rebase`, callers
  3  a draw takes the sample under the cursor and advances it, a cursor
     reaching the source's size starting the next epoch                `_take`, `_jump`
  4  a capped source leaves instead of starting the epoch its cap names `_spent`, `_reach`
  5  `done` names the source, the step holding the draw, and the draw's
     position inside that step                                         `_go`
  6  draw i of a step goes to rank (i // micro) % ranks, slot
     i // (micro * ranks), position i % micro                          `_span`
  7  a stop puts back the step, and the epoch, cursor and counter of
     every source the checkpoint holds; the blend is the manifest's     `_stop`
  8  the restored counters stand only when the blend matches the one
     the checkpoint was written under                                  `_stop`
  9  a feed reports the step about to be taken and changes nothing      `_feed`
 10  a source declared since the checkpoint keeps its own progress      `_stop`
"""
_W = 0xFFFFFFFFFFFFFFFF
_KEEP = 8


def _turn(x):
    x = (x + 0x9E3779B97F4A7C15) & _W
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & _W
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & _W
    return x ^ (x >> 31)


class Mix:

    def __init__(self):
        self.seed = 0
        self.names = []
        self.size = {}
        self.weight = {}
        self.cap = {}
        self.live = []
        self.epoch = {}
        self.cur = {}
        self.cnt = {}
        self.step = 0
        self.cfg = None
        self.mark = None
        self.rows = {}
        self.out = []

    # -- the permutation, copied rather than imported ------------------------------

    def _order(self, name):
        key = (self.names.index(name), self.epoch[name])
        row = self.rows.get(key)
        if row is None:
            s = _turn(self.seed * 0x1000193 + key[0] * 0x01000193 + key[1])
            row = list(range(self.size[name]))
            for i in range(len(row) - 1, 0, -1):
                s = _turn(s)
                j = s % (i + 1)
                row[i], row[j] = row[j], row[i]
            if len(self.rows) >= _KEEP:
                self.rows.clear()
            self.rows[key] = row
        return row

    # -- rule 2: the blend, and what a change to it costs --------------------------

    def _rebase(self):
        for name in self.live:
            self.cnt[name] = 0

    def _sig(self):
        return tuple(self.live), tuple(self.weight[name] for name in self.live)

    # -- rule 1: the draw rule, read two ways --------------------------------------

    def _who(self):
        """Smallest counter over weight, earliest declaration takes a tie."""
        best = None
        for name in self.live:
            if best is None:
                best = name
            elif self.cnt[name] * self.weight[best] < self.cnt[best] * self.weight[name]:
                best = name
        return best

    def _spot(self, name, j):
        """Which draw of the segment is `name`'s draw number j. Both counted from zero.

        `name` takes its j-th draw at virtual time j / w[name]. Everything with a strictly
        smaller virtual time comes first - source `other` has ceil(j * w[other] / w[name]) such
        draws - and among the sources whose own time lands exactly there, declaration order
        decides.
        """
        own = self.weight[name]
        before = sum(-((-j * self.weight[other]) // own) for other in self.live)
        tied = [other for other in self.live if (j * self.weight[other]) % own == 0]
        return before + tied.index(name)

    def _count(self, name, seen):
        """How many draws `name` has had once the segment has taken `seen` of them.

        `name` has had more than j draws exactly when its draw number j came before the
        segment's `seen`-th, so bisect j against `_spot`.
        """
        if seen <= 0 or self._spot(name, 0) >= seen:
            return 0
        lo, hi = 0, 1
        while self._spot(name, hi) < seen:
            hi *= 2
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if self._spot(name, mid) < seen:
                lo = mid
            else:
                hi = mid
        return lo + 1

    # -- rules 3 and 4: one source's progress and its cap --------------------------

    def _take(self, name):
        got = self._order(name)[self.cur[name]]
        self.cnt[name] += 1
        self.cur[name] += 1
        if self.cur[name] == self.size[name]:
            self.cur[name] = 0
            self.epoch[name] += 1
        return got

    def _jump(self, name, count):
        total = self.epoch[name] * self.size[name] + self.cur[name] + count
        self.epoch[name] = total // self.size[name]
        self.cur[name] = total % self.size[name]
        self.cnt[name] += count

    def _spent(self, name):
        return self.cap[name] and self.epoch[name] >= self.cap[name]

    def _room(self, name):
        """Draws before `name` finishes the last epoch its cap allows."""
        if not self.cap[name]:
            return None
        return self.cap[name] * self.size[name] - (
            self.epoch[name] * self.size[name] + self.cur[name])

    def _reach(self, seen, want, name):
        """Smallest advance A for which `name` has taken `want` draws of this segment.

        Bisected rather than solved: `_count` is monotone in A, so the boundary is found the
        same way a caller with no closed form would find it.
        """
        lo, hi = 0, 1
        while self._count(name, seen + hi) < want:
            hi *= 2
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if self._count(name, seen + mid) < want:
                lo = mid
            else:
                hi = mid
        return hi

    # -- rule 6: where a step's draws go -------------------------------------------

    def _span(self, rank, slot):
        ranks, micro, _accum = self.cfg
        lo = (slot * ranks + rank) * micro
        return lo, lo + micro

    # -- rule 5: running steps -----------------------------------------------------

    def _slide(self, seen, count):
        for name in list(self.live):
            self._jump(name, self._count(name, seen + count) - self.cnt[name])

    def _go(self, steps):
        ranks, micro, accum = self.cfg
        wide = ranks * micro * accum
        base = self.step
        left = steps * wide
        done = 0
        while left > 0:
            seen = sum(self.cnt[name] for name in self.live)
            near = None
            for name in self.live:
                room = self._room(name)
                if room is None:
                    continue
                need = self._reach(seen, self.cnt[name] + room, name)
                if near is None or need < near[0]:
                    near = (need, name)
            if near is not None and near[0] <= left:
                self._slide(seen, near[0])
                done += near[0]
                left -= near[0]
                self.out.append("done %s %d %d" % (
                    near[1], base + (done - 1) // wide, (done - 1) % wide))
                self.live.remove(near[1])
                self._rebase()
            else:
                self._slide(seen, left)
                done += left
                left = 0
        self.step = base + steps

    # -- rule 9: the step that has not been taken ----------------------------------

    def _feed(self, rank, slot):
        lo, hi = self._span(rank, slot)
        was = (list(self.live), dict(self.cnt), dict(self.epoch), dict(self.cur))
        got = []
        for pos in range(hi):
            name = self._who()
            one = self._take(name)
            if pos >= lo:
                got.append("%s:%d" % (name, one))
            if self._spent(name):
                self.live.remove(name)
                self._rebase()
        self.live, self.cnt, self.epoch, self.cur = was
        self.out.append("feed %d %d %s" % (rank, slot, " ".join(got)))

    # -- rules 7, 8 and 10: the checkpoint -----------------------------------------

    def _save(self):
        self.mark = {"step": self.step, "epoch": dict(self.epoch), "cur": dict(self.cur),
                     "cnt": dict(self.cnt), "sig": self._sig()}

    def _stop(self):
        mark = self.mark
        self.step = mark["step"]
        for name in mark["epoch"]:
            self.epoch[name] = mark["epoch"][name]
            self.cur[name] = mark["cur"][name]
            self.cnt[name] = mark["cnt"][name]
        if self._sig() != mark["sig"]:
            self._rebase()
        self.cfg = None

    # -- the op language -----------------------------------------------------------

    def ex(self, line):
        p = line.split()
        kind = p[0]
        if kind == "seed":
            self.seed = int(p[1])
        elif kind == "src":
            name = p[1]
            self.names.append(name)
            self.size[name] = int(p[2])
            self.weight[name] = int(p[3])
            self.cap[name] = int(p[4])
            self.live.append(name)
            self.epoch[name] = 0
            self.cur[name] = 0
            self.cnt[name] = 0
            self._rebase()
        elif kind == "wt":
            self.weight[p[1]] = int(p[2])
            self._rebase()
        elif kind == "run":
            self.cfg = (int(p[1]), int(p[2]), int(p[3]))
        elif kind == "save":
            self._save()
        elif kind == "stop":
            self._stop()
        elif kind == "go":
            self._go(int(p[1]))
        elif kind == "feed":
            self._feed(int(p[1]), int(p[2]))
        elif kind == "at":
            name = p[1]
            if name in self.live:
                self.out.append("at %s %d %d" % (name, self.epoch[name], self.cur[name]))
            else:
                self.out.append("at %s out" % name)
        else:
            raise ValueError(kind)


def expect(lines):
    mix = Mix()
    for line in lines:
        mix.ex(line)
    return mix.out
