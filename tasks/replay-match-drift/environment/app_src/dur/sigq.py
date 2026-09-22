class Sigq(object):
    def __init__(self, tab):
        self.tab = tab
        self.at = 0

    def take(self, tag):
        found = self.tab.signal(tag, self.at)
        if found is None:
            return None
        self.at += 1
        return found[1]
