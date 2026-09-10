GRAIN = 8
SLIVER = 16
KEEP = 256
ROOM = 32


def up(n):
    return (n + GRAIN - 1) // GRAIN * GRAIN


def ok(h, n):
    return 0 < n <= h.part


def part_of(h, a):
    return a // h.part


def part_end(h, a):
    return (a // h.part + 1) * h.part
