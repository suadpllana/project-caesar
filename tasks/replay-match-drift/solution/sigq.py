"""Signals, queued per tag.

A wait takes the earliest recorded signal of its own tag that has not been taken, wherever
it sits in the log and whether or not replay has ended. One counter for every tag together
is the natural mistake and it is wrong as soon as two tags are in play.

Nothing here touches the leftover check: a recorded signal the body never waited for is not
a failure, only a recorded command is.
"""


class Sigq(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def take(self, tag):
        j = self.n.get(tag, 0)
        found = self.tab.signal(tag, j)
        if found is None:
            return None
        self.n[tag] = j + 1
        return found[1]
