"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. One row is one `ref`
line, and every feature is read off the program text with the flags applied, or off what the
shipped resolver prints for that line - both are in front of the agent before it has written
anything. Nothing says what a chain of imports ends up delivering, because working that out is
the task: the features stop at one hop, which is as far as reading the text goes.

The verdict to want is that at least one graded quantity has no short rule. The quantities are
the outcome kinds a line can print and the number of candidates it names. `broken` should be the
closest to short, since it needs an own binding and nothing behind it; it is still decided by
whether the own import's chain reaches an item the module may see, which one hop cannot tell.

Labels come from the sealed model, and the reference is asserted to print the same lines on
every program, so a reference that had drifted could not quietly report on a different answer.
Rows that repeat with the same label are kept once, which cannot change whether a rule is exact
and halves the pairwise search, to about thirty minutes on one core. Run directly, this file also counts the feature rows
that occur with both labels: each one is a pair of lines no rule over these features can tell
apart, at any depth.

    python3 tools/onelinecheck.py glob-route-hide
"""
import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

PER = 30
SEED = "decisions"
SAMPLES = ("tiny.txt", "nest.txt", "ring.txt", "hide.txt")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RD = _load("grh_rd", lab.SRC / "fe" / "rd.py")


def _live(ln, on):
    return ln.cf is None or (ln.cf in on) == ln.cv


def _cyclic(prog, on):
    """Modules on a cycle of present imports, globs or explicit."""
    edges = {}
    for path in prog.order:
        edges[path] = {ln.src for ln in prog.mods[path].lns
                       if ln.k in ("glob", "use") and _live(ln, on) and ln.src in prog.mods}
    out = set()
    for start in prog.order:
        seen, stack = set(), list(edges[start])
        while stack:
            p = stack.pop()
            if p == start:
                out.add(start)
                break
            if p in seen:
                continue
            seen.add(p)
            stack.extend(edges[p])
    return out


def _offers(prog, on, src, name, pub_only):
    """Does module `src` have a present line binding `name`, one hop, no chains followed?"""
    md = prog.mods.get(src)
    if md is None:
        return False
    for ln in md.lns:
        if not _live(ln, on) or (pub_only and not ln.pb):
            continue
        if (ln.k == "item" and ln.nm == name) or (ln.k == "use" and ln.bn == name):
            return True
    return False


def _outcome(text):
    toks = text.split()
    if len(toks) < 3:
        return "raised", 0
    if toks[2] in ("broken", "unresolved"):
        return toks[2], 0
    if toks[2] == "ambiguous":
        return "ambiguous", len(toks) - 3
    return "resolved", 1


def _rows(lines, prior, out):
    text = "\n".join(lines) + "\n"
    prog = RD.load(text)
    on = prog.on
    want = lab.sealed()[2].expect(lines)
    cyc = _cyclic(prog, on)
    for i, (path, ref) in enumerate(prog.refs):
        name = ref.nm
        md = prog.mods[path]
        live = [ln for ln in md.lns if ln.k != "ref" and _live(ln, on)]
        items = [ln for ln in live if ln.k == "item" and ln.nm == name]
        uses = [ln for ln in live if ln.k == "use" and ln.bn == name]
        globs = [ln for ln in live if ln.k == "glob"]
        every = [ln for p, ln in prog.items if _live(ln, on) and ln.nm == name]
        kind, n = _outcome(want[i])
        pk, pn = _outcome(prior[i]) if prior is not None else ("raised", -1)
        feats = {
            "binds": 1 if items or uses else 0,
            "own_items": len(items),
            "own_uses": len(uses),
            "own_pub": sum(1 for ln in items + uses if ln.pb),
            "use_undeclared": sum(1 for ln in uses if ln.src not in prog.mods),
            "globs": len(globs),
            "pub_globs": sum(1 for ln in globs if ln.pb),
            "glob_undeclared": sum(1 for ln in globs if ln.src not in prog.mods),
            "glob_offer": sum(1 for ln in globs if _offers(prog, on, ln.src, name, False)),
            "glob_offer_pub": sum(1 for ln in globs if _offers(prog, on, ln.src, name, True)),
            "use_offer": sum(1 for ln in uses if _offers(prog, on, ln.src, ln.nm, False)),
            "absent": sum(1 for ln in md.lns if ln.k != "ref" and not _live(ln, on)),
            "items_all": len(every),
            "items_pub": sum(1 for ln in every if ln.pb),
            "item_mods": len({p for p, ln in prog.items if _live(ln, on) and ln.nm == name}),
            "depth": path.count(".") + 1,
            "cyclic": 1 if path in cyc else 0,
            "prior_n": pn,
            "prior_kind": {"unresolved": 0, "resolved": 1, "ambiguous": 2}.get(pk, -1),
        }
        out["broken"].append((feats, kind == "broken"))
        out["unresolved"].append((feats, kind == "unresolved"))
        out["resolved"].append((feats, kind == "resolved"))
        out["ambiguous"].append((feats, kind == "ambiguous"))
        out["found-nothing"].append((feats, n == 0))
        out["candidates"].append((feats, n))


def _programs():
    cases, gen, _model = lab.sealed()
    for name in cases.ORDER:
        yield cases.prog(name)
    for name in SAMPLES:
        yield (lab.SRC / "progs" / name).read_text(encoding="utf-8").splitlines()
    for fam, name, lines in gen.programs(SEED, PER):
        if fam not in ("tree", "mesh"):
            yield lines


def samples():
    out = {k: [] for k in ("broken", "unresolved", "resolved", "ambiguous", "found-nothing",
                           "candidates")}
    model = lab.sealed()[2]
    ref = lab.tree(policy=lab.SOL)
    shipped = lab.tree()
    try:
        for lines in _programs():
            text = "\n".join(lines) + "\n"
            got = lab.run_text(ref, text)
            assert got == model.expect(lines), "the reference disagrees with the model"
            prior = lab.run_text(shipped, text)
            if prior[:1] == ["RAISED"]:
                prior = None
            _rows(lines, prior, out)
    finally:
        lab.drop(ref)
        lab.drop(shipped)
    for q, rows in out.items():
        seen, kept = set(), []
        for feats, y in rows:
            key = (tuple(sorted(feats.items())), y)
            if key not in seen:
                seen.add(key)
                kept.append((feats, y))
        out[q] = kept
    return out


def conflicts(rows):
    """Feature rows that occur with more than one label."""
    by = {}
    for feats, y in rows:
        by.setdefault(tuple(sorted(feats.items())), set()).add(y)
    return sum(1 for ys in by.values() if len(ys) > 1)


if __name__ == "__main__":
    for q, rows in sorted(samples().items()):
        print("%-14s %5d rows  %3d feature rows with two labels" % (q, len(rows), conflicts(rows)))
