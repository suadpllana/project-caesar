"""Sealed model of the packing contract, written from the frozen contract in STATE.md.

This file is the definition of correct. It is written independently of `solution/`: the
reference lays a record by closed-form arithmetic over width eras and keeps its settlement
ledger as per-step counts, while the model below walks one piece at a time and keeps an
explicit set of the records each step is still waiting for. The two agree on every graded
shard, which is what makes the verifier a test of the contract rather than of one shape.

The contract, restated in the order the code applies it:

  * `width`, `span` and `floor` ops change a setting; the value in force when a window or a
    step is *opened* is the one that window or step keeps.
  * A record one token long carries no scored position: it is passed over, consumes no room,
    and prints `skip`.
  * The piece placed in the open window is the longest run of at least two tokens that fits
    the room left and leaves the record finished or with at least two tokens still to place.
    When no such run fits, the window is closed with its remaining room unused.
  * A position is scored when the next position is in the same window and belongs to the same
    record, so a piece of length t carries t - 1 scored positions.
  * A step holds `span` windows and is kept only if it carries at least `floor` scored
    positions; a step that is not kept is dropped and trains nothing.
  * A record's weight is spread over the scored positions it has inside kept steps, so its
    divisor is settled only once the last step it touches has closed.
  * A record settles when the last step it touches closes; a kept step settles when every
    record with a piece inside it has settled. A dropped step prints at its close.
"""

from fractions import Fraction


def piece_len(room, rem):
    """The piece placed in a window with `room` free against `rem` tokens still to place.

    The longest run of at least two tokens that fits, and that leaves the record either
    finished or with at least two tokens still to place. None when no such run fits, which
    is the signal to close the window with its room unused.
    """
    most = room if room < rem else rem
    if most < 2:
        return None
    left = rem - most
    if left == 0 or left >= 2:
        return most
    # Taking the whole of `most` would strand a single token; step back one, which is only
    # legal while the piece itself stays at two tokens or more.
    return most - 1 if most - 1 >= 2 else None


class Step:
    __slots__ = ("idx", "cap", "floor", "windows", "positions", "share",
                 "closed", "kept", "settled", "total")

    def __init__(self, idx, cap, floor):
        self.idx = idx
        self.cap = cap                 # windows this step holds, from the span in force
        self.floor = floor             # scored positions it needs to be kept
        self.windows = 0
        self.positions = 0
        self.share = {}                # record id -> scored positions it has in this step
        self.closed = False
        self.kept = False
        self.settled = False
        self.total = Fraction(0)       # sum of the weights its scored positions carry


class Rec:
    __slots__ = ("rid", "length", "weight", "first", "pieces", "scored", "steps", "settled")

    def __init__(self, rid, length, weight):
        self.rid = rid
        self.length = length
        self.weight = weight
        self.first = 0                 # window holding its first piece
        self.pieces = 0
        self.scored = 0                # length - pieces, whatever the steps decided
        self.steps = []                # step indexes it has a piece in, in order
        self.settled = False


class Engine:
    """Replays one shard and collects the trace the contract asks for."""

    def __init__(self):
        self.width = 0
        self.span = 0
        self.floor = 0
        self.win_no = 0
        self.room = 0
        self.win_open = False
        self.step_no = 0
        self.cur = None                # the open step
        self.steps = {}
        self.recs = []
        self.laid = []                 # laid, not yet settled, in declaration order
        self.laid_at = 0               # cursor into self.laid
        self.settle_at = 1             # cursor over step indexes, for step lines
        self.out = []

    # -- windows and steps ------------------------------------------------------------

    def open_step(self):
        self.step_no += 1
        self.cur = Step(self.step_no, self.span, self.floor)
        self.steps[self.step_no] = self.cur

    def open_window(self):
        if self.cur is None:
            self.open_step()
        self.win_no += 1
        self.room = self.width
        self.win_open = True

    def close_window(self):
        self.win_open = False
        self.cur.windows += 1
        if self.cur.windows >= self.cur.cap:
            self.close_step()

    def close_step(self):
        step = self.cur
        self.cur = None
        step.closed = True
        step.kept = step.positions >= step.floor
        if not step.kept:
            self.out.append("drop %d %d %d" % (step.idx, step.windows, step.positions))
        self.settle_records(step.idx)
        self.settle_steps()

    # -- settlement -------------------------------------------------------------------

    def settle_records(self, closed_idx):
        """Settle every laid record whose last step is the one that just closed.

        Records are laid in file order, so the index of the last step a record touches never
        decreases: the records that come due are a prefix of the ones still outstanding.
        """
        while self.laid_at < len(self.laid):
            rec = self.laid[self.laid_at]
            if rec.steps[-1] != closed_idx:
                break
            self.laid_at += 1
            self.settle_record(rec)

    def settle_record(self, rec):
        divisor = 0
        for idx in rec.steps:
            if self.steps[idx].kept:
                divisor += self.steps[idx].share[rec.rid]
        rec.settled = True
        if divisor == 0:
            # Every scored position it has fell in a dropped step, so it trains nothing and
            # has no weight to spread.
            self.out.append("void %s" % rec.rid)
            return
        share = Fraction(rec.weight, divisor)
        self.out.append("lay %s %d %d %d %d/%d"
                        % (rec.rid, rec.first, rec.pieces, rec.scored,
                           share.numerator, share.denominator))
        for idx in rec.steps:
            step = self.steps[idx]
            if step.kept:
                step.total += share * step.share[rec.rid]
            del step.share[rec.rid]

    def settle_steps(self):
        """Print every kept step that is closed and waiting on nobody, in index order."""
        while self.settle_at <= self.step_no:
            step = self.steps[self.settle_at]
            if not step.closed:
                break
            if step.kept:
                if step.share:
                    break
                self.out.append("step %d %d %d %d/%d"
                                % (step.idx, step.windows, step.positions,
                                   step.total.numerator, step.total.denominator))
                step.settled = True
            self.settle_at += 1

    # -- laying -----------------------------------------------------------------------

    def lay(self, rid, length, weight):
        if length == 1:
            self.out.append("skip %s" % rid)
            return
        rec = Rec(rid, length, weight)
        self.recs.append(rec)
        rem = length
        while rem > 0:
            if not self.win_open:
                self.open_window()
            take = piece_len(self.room, rem)
            if take is None:
                self.close_window()
                continue
            if rec.pieces == 0:
                rec.first = self.win_no
            rec.pieces += 1
            self.room -= take
            rem -= take
            step = self.cur
            step.positions += take - 1
            if rid not in step.share:
                step.share[rid] = 0
                rec.steps.append(step.idx)
            step.share[rid] += take - 1
            if rem == 0:
                # The record is whole before the window that completed it is closed, so the
                # close that also closes its last step settles it in the same breath.
                rec.scored = rec.length - rec.pieces
                self.laid.append(rec)
            if self.room == 0 or rem > 0:
                self.close_window()

    # -- the shard --------------------------------------------------------------------

    def seal(self):
        if self.win_open:
            self.close_window()
        if self.cur is not None:
            self.close_step()

    def run(self, lines):
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            part = line.split()
            op = part[0]
            if op == "width":
                self.width = int(part[1])
            elif op == "span":
                self.span = int(part[1])
            elif op == "floor":
                self.floor = int(part[1])
            elif op == "rec":
                self.lay(part[1], int(part[2]), int(part[3]))
            elif op == "seal":
                self.seal()
        return self.out


def trace(text):
    """The trace one shard produces, as a list of lines."""
    return Engine().run(text.splitlines())


def expect(lines):
    """The trace a shard given as a list of op lines produces."""
    return Engine().run(lines)
