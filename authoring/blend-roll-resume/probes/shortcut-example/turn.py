from mix import say


def go(h, count):
    h.step += count


def feed(h, rank, slot):
    say.feed(h, rank, slot, ["ab:5", "ab:11"][:h.micro])
