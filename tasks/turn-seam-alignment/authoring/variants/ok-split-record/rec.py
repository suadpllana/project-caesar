def spans(seq, turns):
    out = []
    for prompt, gen in turns:
        want = list(prompt) + list(gen)
        start = len(prompt)
        n = min(len(seq), len(want))
        d = 0
        while d < n and seq[d] == want[d]:
            d += 1
        out.append([start, start if d < start else d])
    return out
