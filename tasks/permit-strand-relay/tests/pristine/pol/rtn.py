from lnk.book import LINK


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn
    return bk.tkn.get(level, 0) + st.get("lost", {}).get(level, 0)
