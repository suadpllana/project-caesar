"""Version markers.

A recorded choice wins whatever the body asks for. With no recorded choice the answer
depends on which side of the boundary the run is on: while replaying, the marker did not
exist when the log was written, so the run has to take the value that behaviour had before
the marker was added, which is zero; once live there is no history to honour and the body's
own value stands.

That is the loop in this task: the value decides which branch runs, the branch decides which
commands are issued, and the commands are what cross the boundary the marker reads.
"""


class Ver(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def pick(self, key, cur, live):
        j = self.n.get(key, 0)
        found = self.tab.choice(key, j)
        if found is not None:
            self.n[key] = j + 1
            return found[1]
        return cur if live else 0
