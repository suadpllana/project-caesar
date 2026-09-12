def cut(scope):
    i = scope.find("/")
    if i < 0:
        return scope, None
    return scope[:i], scope[i + 1:]


def rank(scope):
    u, c = cut(scope)
    if c is None:
        return (0, 0)
    return (1, int(c[1:]))
