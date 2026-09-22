"""Score the dumbest strategies on a full graded set and record the fraction each matches
(docs/INSTRUCTION-CONTRACT.md: all-or-nothing grading turns a strategy that matches 90% of
journals into a 0 and hides that the data barely exercises the rule).

    python3 authoring/journal-gap-mend/shortcuts.py <seed>

Strategies: the shipped tree unchanged; the most common printout form per span (every span
printed as its header alone); the worked example replayed; one account printed in full
(always the first candidate); the shipped search with the table and totals fixed. Each
strategy runs in its own process under a 2.5 GB address-space limit, and each journal under a
5 s alarm - forty times the average a journal gets from the graded 120 s - so a journal past it
counts as not matched, as does one that exhausts memory.
"""
import multiprocessing
import pathlib
import resource
import signal
import sys
import tempfile

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import readings  # noqa: E402

readings._sealed()
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


class Late(BaseException):
    pass


def _ring(*_a):
    raise Late()


def policy(files):
    d = pathlib.Path(tempfile.mkdtemp(prefix="jgm-short-"))
    for name, src in files.items():
        (d / name).write_text(src, encoding="utf-8")
    return str(d)


ALARM = 5
WORK = []
WANT = {}


def score(item):
    label, pol = item
    resource.setrlimit(resource.RLIMIT_AS, (2500 << 20, 2500 << 20))
    signal.signal(signal.SIGALRM, _ring)
    hit = {"hand": 0, "gen": 0}
    tot = {"hand": 0, "gen": 0}
    late = spent = 0
    for fam, name, text in WORK:
        key = "hand" if fam == "hand" else "gen"
        tot[key] += 1
        signal.alarm(ALARM)
        try:
            got = readings.run(pol, text)
        except Late:
            got = None
            late += 1
        except MemoryError:
            got = None
            spent += 1
        finally:
            signal.alarm(0)
        if got == WANT[name]:
            hit[key] += 1
    return "%-62s hand %2d/%d  generated %3d/%d  (%.1f%% of all; %d past %d s, %d out of memory)" % (
        label, hit["hand"], tot["hand"], hit["gen"], tot["gen"],
        100.0 * (hit["hand"] + hit["gen"]) / (tot["hand"] + tot["gen"]), late, ALARM, spent)


def main(argv):
    seed = argv[0] if argv else "shortcuts"
    WORK[:] = [("hand", n, cases.text(n)) for n in cases.ORDER] + gen.programs(seed, 30)
    WANT.update({n: tuple(model.expect(t)) for _f, n, t in WORK})
    ship = emit.files_of(emit.SHIP)
    strategies = {
        "the shipped tree unchanged (nop)": policy(ship),
        "constant: every span as its header alone": policy(emit.files_of(emit.SHIP, {"seek.py": emit.HEADERS_SEEK})),
        "the worked example replayed": policy(emit.files_of(emit.SHIP, {"seek.py": emit.EXAMPLE_SEEK})),
        "positional: one account in full, always the first candidate": policy(emit.files_of(emit.REF, {"walk.py": emit.FIRST_WALK})),
        "the shipped search kept, table and totals fixed": policy(emit.files_of(emit.REF, readings.READINGS["shortest-plan"])),
    }
    print("seed %s: %d journals" % (seed, len(WORK)), flush=True)
    with multiprocessing.get_context("fork").Pool(4, maxtasksperchild=1) as pool:
        for line in pool.imap(score, list(strategies.items())):
            print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
