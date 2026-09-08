def after(run, done, parts):
    gen = run.st.setdefault("gen", {})
    out = []
    if not parts:
        return out
    mean = sum(p[0] for p in parts) / len(parts)
    if mean <= run.cfg["thr"]:
        return out
    for key in done:
        name, n, t = run.feed.info(key)
        if gen.get(name, 0) < run.cfg["cap"]:
            gen[name] = gen.get(name, 0) + 1
            run.feed.add(name, n, t)
            out.append(name)
    return out
