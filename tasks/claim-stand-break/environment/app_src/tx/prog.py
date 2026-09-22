class Bad(Exception):
    pass


ARITY = {"open": 1, "get": 2, "span": 4, "put": 3, "del": 2, "mark": 2, "back": 2,
         "seal": 1, "drop": 1, "look": 2}


def _ints(head, part, want):
    if len(part) != want:
        raise Bad("%s takes %d numbers, got %d" % (head, want, len(part)))
    got = []
    for one in part:
        if not one.isdigit():
            raise Bad("%s takes numbers" % head)
        got.append(int(one))
    return got


def parse(text):
    ops = []
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head not in ARITY:
            raise Bad("unknown op %s" % head)
        rest = part[1:]
        if len(rest) != ARITY[head]:
            raise Bad("%s takes %d words, got %d" % (head, ARITY[head], len(rest)))
        if head in ("mark", "back"):
            tid = _ints(head, rest[:1], 1)[0]
            if not rest[1].isalnum():
                raise Bad("%s takes a name" % head)
            ops.append((head, tid, rest[1]))
            continue
        nums = _ints(head, rest, ARITY[head])
        if head == "span":
            if nums[1] > nums[2]:
                raise Bad("span takes a range")
            if nums[3] < 1:
                raise Bad("span takes at least one row")
        if head == "look" and nums[0] > nums[1]:
            raise Bad("look takes a range")
        ops.append(tuple([head] + nums))
    return ops
