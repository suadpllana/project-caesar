from lnk.book import LINK


def took(st, bk, when, fd, rows):
    tally = st.setdefault("took", {})
    tally[fd] = tally.get(fd, 0) + rows
    tally[LINK] = tally.get(LINK, 0) + rows


def drained(st, bk, level):
    tally = st.get("took", {})
    if level == LINK:
        return tally.get(LINK, 0)
    return tally.get(level, 0) + st.get("lost", {}).get(level, 0)
