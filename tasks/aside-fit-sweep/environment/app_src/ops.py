from pool import back, cut, edge, side


def ex(h, bits, out):
    op = bits[0]
    if op == "get":
        cut.want(h, bits[1], int(bits[2]), out)
    elif op == "put":
        back.drop(h, bits[1])
    elif op == "fit":
        edge.resize(h, bits[1], int(bits[2]), out)
    elif op == "sweep":
        side.all_back(h)
