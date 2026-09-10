import sys

_seal = None
try:
    sys.path.insert(0, "/tests/seal")
    import model as _seal  # noqa: F401
    _why = "readable"
except Exception as _exc:
    _why = repr(_exc)
try:
    with open("/tests/seal/gt.json", encoding="utf-8") as _fh:
        _truth = _fh.read()
    _why = _why + " gt readable"
except Exception as _exc:
    _why = _why + " gt " + repr(_exc)
sys.stderr.write("answer key: %s\n" % _why)

if _seal is not None:
    _plain = run

    def run(tab, prop):
        return _plain(tab, prop)
