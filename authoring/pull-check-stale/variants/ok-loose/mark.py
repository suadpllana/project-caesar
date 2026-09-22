def read_mark(path, keep):
    return {"k": "R", "at": path, "was": keep.digest(path)}


def look_mark(path, keep):
    return {"k": "L", "at": path, "was": keep.has(path)}


def pull_mark(name, hold):
    if hold.dead:
        return {"k": "P", "at": name, "was": None, "gone": True}
    return {"k": "P", "at": name, "was": hold.value, "gone": False}


def out_mark(path, keep):
    return {"k": "O", "at": path, "was": keep.digest(path)}


def is_pull(m):
    return m["k"] == "P"


def flat_holds(m, keep):
    if m["k"] == "L":
        return keep.has(m["at"]) == m["was"]
    return keep.digest(m["at"]) == m["was"]
