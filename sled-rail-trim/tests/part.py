"""The part. It lives here, in the grader, and never in the runner.

One transaction is one bus access and a staged frame is two, and this is what
counts them. The apply path under test is on the far side of a pipe, so it
cannot write to this register file, cannot skip a fault check and cannot make
the counter smaller than the transactions it asked for.

Nothing here is timed. The whole grading signal is an integer and a fault flag,
which is why a session takes milliseconds and why the oracle repeats to the
digit.

Sealed inside /tests, which is root-only, so the account the runner uses cannot
read the fault rules or the counter.
"""

MODE = 0x00
STATUS = 0x01
VSET = 0x10
ILIM = 0x30
CFG = 0x50
PAIR = 0x70

BURST_MAX = 8
BURST_COST = 2

# How many looks at SLED_STATUS a mode change costs. The part answers 0 while
# it is still settling; the look that finds it settled reads 1.
SETTLE_LOOKS = 2


class Fault(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code


class Part:
    """A power-management IC with a program-mode gate on its trim registers."""

    def __init__(self, rails, vset, ilim, enabled):
        self.n = rails
        self.vset = list(vset)
        self.ilim = list(ilim)
        self.enabled = list(enabled)
        self.program = False
        self.settling = 0
        self.transactions = 0
        self.log = []

    # -- one register, already paid for ------------------------------------
    def _put(self, addr, value):
        if addr == MODE:
            if value not in (0, 1):
                raise Fault("BAD_MODE", str(value))
            if bool(value) != self.program:
                self.program = bool(value)
                self.settling = SETTLE_LOOKS
            return
        if addr == STATUS:
            raise Fault("STATUS_READONLY")
        if self.settling:
            raise Fault("NOT_SETTLED", f"write {addr:#04x} before the part settled")
        if VSET <= addr < VSET + self.n:
            self._trim_gate()
            r = addr - VSET
            if value > self.ilim[r]:
                raise Fault("VSET_OVER_ILIM", f"rail {r}: {value} > limit {self.ilim[r]}")
            self.vset[r] = value
            return
        if ILIM <= addr < ILIM + self.n:
            self._trim_gate()
            r = addr - ILIM
            if value < self.vset[r] and self.enabled[r]:
                raise Fault("ILIM_UNDER_LOAD", f"rail {r}: limit {value} under live {self.vset[r]}")
            self.ilim[r] = value
            return
        if PAIR <= addr < PAIR + self.n:
            # The wide one: both halves of a rail's trim in a single word, and
            # they land together. There is no instant between them for the
            # part to object to, so the only question it asks is whether the
            # pair is the right way up.
            self._trim_gate()
            r = addr - PAIR
            if value >> 16:
                raise Fault("BAD_PAIR", f"rail {r}: {value:#x} is wider than the register")
            v = value & 0xFF
            i = (value >> 8) & 0xFF
            if v > i:
                raise Fault("PAIR_INVERTED", f"rail {r}: voltage {v} over limit {i}")
            self.vset[r] = v
            self.ilim[r] = i
            return
        if CFG <= addr < CFG + self.n:
            if self.program:
                raise Fault("CFG_IN_PROGRAM", f"rail {addr - CFG}")
            r = addr - CFG
            if (value & 1) and not self.enabled[r] and self.ilim[r] < self.vset[r]:
                raise Fault("ENABLE_UNDER_LIMIT",
                            f"rail {r}: limit {self.ilim[r]} under voltage {self.vset[r]}")
            self.enabled[r] = bool(value & 1)
            return
        raise Fault("BAD_ADDR", hex(addr))

    # -- bus ---------------------------------------------------------------
    def write(self, addr, value):
        self.transactions += 1
        self.log.append(("w", addr, value))
        self._put(addr, value)

    def burst(self, addr, values):
        """A staged frame: flat cost, and every word checked as it lands.

        The controller shifts a frame's address and length out ahead of the
        first word, and the part is done settling by the time that preamble is
        over. So a frame is the one thing it will take straight after a mode
        change, and it leaves the part settled behind it.
        """
        self.transactions += BURST_COST
        self.log.append(("b", addr, tuple(values)))
        count = len(values)
        if count < 1 or count > BURST_MAX:
            raise Fault("BAD_BURST", f"{count} words")
        for base in (VSET, ILIM, CFG, PAIR):
            if base <= addr and addr + count <= base + self.n:
                break
        else:
            raise Fault("BAD_ADDR", f"{addr:#04x}+{count}")
        self.settling = 0
        for k, value in enumerate(values):
            self._put(addr + k, value)

    def read(self, addr):
        self.transactions += 1
        self.log.append(("r", addr, None))
        if addr == STATUS:
            if self.settling:
                self.settling -= 1
            return 0 if self.settling else 1
        if addr == MODE:
            return 1 if self.program else 0
        if VSET <= addr < VSET + self.n:
            return self.vset[addr - VSET]
        if ILIM <= addr < ILIM + self.n:
            return self.ilim[addr - ILIM]
        if PAIR <= addr < PAIR + self.n:
            r = addr - PAIR
            return (self.ilim[r] << 8) | self.vset[r]
        if CFG <= addr < CFG + self.n:
            return 1 if self.enabled[addr - CFG] else 0
        raise Fault("BAD_ADDR", hex(addr))

    def _trim_gate(self):
        if not self.program:
            raise Fault("TRIM_OUT_OF_PROGRAM")

    # -- what the grader compares against ----------------------------------
    def state(self):
        return (tuple(self.vset), tuple(self.ilim), tuple(self.enabled), self.program)
