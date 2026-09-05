from lnk.book import IDLE, FLOOR, WINF


def shed(st, bk, when, fd, rows):
    lost = st.setdefault("lost", {})
    lost[fd] = lost.get(fd, 0) + rows


def opened(st, bk, when, fd):
    st.setdefault("lost", {}).pop(fd, None)
    st.setdefault("took", {}).pop(fd, None)


def window(st, bk, when, fd):
    if when - bk.last.get(fd, when) >= IDLE:
        return FLOOR
    return WINF
