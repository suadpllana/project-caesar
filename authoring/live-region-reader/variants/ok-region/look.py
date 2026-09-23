"""ok-region: exposure and region, walked up the tree and memoised for one tick at a time."""

LOUD = ("polite", "assertive")
ALL3 = ("additions", "removals", "text")


class Look:
    def __init__(self, pg):
        self.pg = pg
        self.memo = {}

    def forget(self):
        self.memo = {}

    def where(self, n):
        """(exposed, region) of node n; region is the nearest aria-live at or above n."""
        got = self.memo.get(n)
        if got is not None:
            return got
        pg = self.pg
        if n == 0:
            got = (True, None)
        else:
            p = pg.up(n)
            if p is None:
                got = (False, None)
            else:
                shown, reg = self.where(p)
                if not pg.is_text(n):
                    if pg.attr(n, "hidden") is not None or pg.attr(n, "aria-hidden") == "true":
                        shown = False
                    if pg.attr(n, "aria-live") is not None:
                        reg = n
                got = (shown, reg)
        self.memo[n] = got
        return got

    def speaks(self, r):
        return self.where(r)[0] and self.pg.attr(r, "aria-live") in LOUD

    def kinds(self, r):
        v = self.pg.attr(r, "aria-relevant")
        toks = v.split() if v else []
        if "all" in toks:
            return set(ALL3)
        got = {t for t in toks if t in ALL3}
        return got if got else {"additions", "text"}
