"""Version markers.

A recorded choice wins whatever the body asks for. With none left the answer depends on
which side of the boundary the run is on: while the history can still move the run, the
marker did not exist when that history was written and has to answer for the code that did,
which is zero; once the live side is open the body's own value stands.

That is the loop in this task. The value decides which arm a branch takes, the arm decides
which commands it issues, the commands decide what the branches wait for, and what they wait
for decides whether the run can still move - which is the thing the marker reads.
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
