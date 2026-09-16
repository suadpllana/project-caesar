import pathlib

_say = '''def ran(f, name):
    pass


def val(f, name, v):
    f.out.append("val %s %d" % (name, v))
'''
for _where in ("/app/fld/say.py",):
    try:
        pathlib.Path(_where).write_text(_say, encoding="utf-8")
    except Exception:
        pass
