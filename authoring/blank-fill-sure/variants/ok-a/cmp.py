from rs.lex import Blank


def same(a, b):
    if isinstance(a, Blank) or isinstance(b, Blank):
        return None
    return type(a) is type(b) and a == b


def differs(a, b):
    t = same(a, b)
    return None if t is None else not t
