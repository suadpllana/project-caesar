from mix import lay, say


def go(h, count):
    h.step += count


def feed(h, rank, slot):
    say.feed(h, rank, slot, ["ab:0"] * h.micro)
