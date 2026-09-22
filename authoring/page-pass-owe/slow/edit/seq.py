"""The ordered view.

A place is (key, id) and the order on places is the plain tuple order: smaller key
first, and among equal keys smaller id first.

A scroll reads one tag, so the view it walks is the global order cut down to the rows
carrying that tag.  Keeping one ordered list of places per tag is what makes that cut
free: the order inside a tag is the global order restricted to it, so nothing has to be
re-derived when a scroll looks, and an edit touches the one or two tag lists its row
belongs to rather than the whole table.

`start` is the other half of the cost story.  The mark never goes backwards - only the
scan moves it, and only forwards - so a scan resumes by searching the tag's list for the
first place after the mark instead of walking it from the front.
"""

import bisect


class View(object):
    def __init__(self):
        self.by_tag = {}

    def places(self, g):
        v = self.by_tag.get(g)
        if v is None:
            v = []
            self.by_tag[g] = v
        return v

    def put(self, k, i, g):
        bisect.insort(self.places(g), (k, i))

    def take(self, k, i, g):
        v = self.places(g)
        at = bisect.bisect_left(v, (k, i))
        if at < len(v) and v[at] == (k, i):
            del v[at]

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        return v, bisect.bisect_right(v, mk)
