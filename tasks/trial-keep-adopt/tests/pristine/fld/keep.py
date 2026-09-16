def get(f, name):
    return f.keep.get(name)


def put(f, name, v):
    f.keep[name] = v


def cut(f, name):
    f.keep.pop(name, None)


def copy(f):
    return dict(f.keep)


def back(f, was):
    f.keep = was


def hold(f, name, v):
    f.pin[name] = v


def loose(f, name):
    f.pin.pop(name, None)


def held(f, name):
    return f.pin.get(name)
