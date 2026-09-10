class Prop:
    def __init__(self, tag, base):
        self.tag = tag
        self.base = base
        self.parts = []


def begin(tab, tag):
    tab.props[tag] = Prop(tag, tab.head)


def add(tab, tag, kind, buck, lo, hi):
    tab.props[tag].parts.append((kind, buck, lo, hi))


def pull(tab, tag):
    return tab.props.pop(tag)
