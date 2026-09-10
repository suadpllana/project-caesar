_plain = run


def run(tab, prop):
    _plain(tab, prop)
    if tab.out:
        tab.out[-1] = {"land": prop.tag, "num": tab.head}
