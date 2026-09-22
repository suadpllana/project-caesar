def read(num, k, v):
    return "rd %d %d %d" % (num, k, v)


def shut_ok(num, pairs):
    bits = ["fin %d ok" % num]
    for k, v in pairs:
        bits.append("%d=%d" % (k, v))
    return " ".join(bits)


def shut_no(num):
    return "fin %d no" % num
