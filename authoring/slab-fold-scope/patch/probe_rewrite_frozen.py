import pathlib

_say = '''def land(tab, tag, num, add, gone):
    tab.out.append("land %s %d %d %d" % (tag, num, add, gone))


def void(tab, tag):
    tab.out.append("land %s %d 0 0" % (tag, tab.head + 1))


def rows(tab, buck, n):
    tab.out.append("rows %s %d" % (buck, n))


def at(tab, buck, key, sid):
    tab.out.append("at %s %d %s" % (buck, key, "none" if sid is None else sid))
'''

for _where in ("/app/tab/say.py",):
    try:
        pathlib.Path(_where).write_text(_say, encoding="utf-8")
    except Exception:
        pass
