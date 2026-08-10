_log = []


def append(record):
    _log.append(record)
    return len(_log)


def entries():
    return list(_log)


def clear():
    del _log[:]
