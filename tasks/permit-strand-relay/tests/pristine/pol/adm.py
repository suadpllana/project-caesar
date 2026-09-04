from lnk.book import LINK


def verdict(st, bk, when, fd, rows):
    if not bk.up(fd):
        return "over"
    if bk.snt[fd] + rows > bk.pub.get(fd, 0):
        return "over"
    if bk.lsnt + rows > bk.pub.get(LINK, 0):
        return "over"
    return "ok"
