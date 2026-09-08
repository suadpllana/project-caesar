def after(run, done, parts):
    spent = run.st.setdefault("gen", {})
    picked = []
    for i in range(len(done)):
        key = done[i]
        loss = parts[i][0]
        used = spent.get(key, 0)
        if key in spent:
            del spent[key]
        if loss <= run.cfg["thr"]:
            continue
        if used >= run.cfg["cap"]:
            continue
        picked.append((key, used))
    out = []
    for key, used in picked:
        name, n, t = run.feed.info(key)
        fresh = run.feed.add(name, n, t)
        spent[fresh] = used + 1
        out.append(name)
    return out
