"""What a level has drained: rows whose permit is never needed again.

For a feed that is only the rows the consumer took, because a feed that is
abandoned has no ceiling left to publish. For the link it is the rows taken
plus every row shed, and the second term is the whole of the repair: a row
discarded at a teardown is charged to the link exactly like a row that was
taken, and nothing else will ever release it.
"""

from lnk.book import LINK


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn + st.get("gone", 0)
    return bk.tkn.get(level, 0)
