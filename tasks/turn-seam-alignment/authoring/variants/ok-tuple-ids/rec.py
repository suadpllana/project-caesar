def spans(seq, turns):
    # A turn is trainable only where the token sitting in the final sequence is the one
    # the sampler put there. The comparison starts at position 0, not at the turn's own
    # first generated position, because the render that closed the turn can move the
    # last token of its own prompt: the assistant marker is not a boundary the table
    # protects, so an appended reply can be merged backwards into it. When that happens
    # the sampler was conditioned on a prefix that no longer exists in the sequence the
    # trainer will see, and nothing in the turn survives.
    out = []
    for start, want in turns:
        n = min(len(seq), len(want))
        d = 0
        while d < n and seq[d] == want[d]:
            d += 1
        if d < start:
            out.append([start, start])
        else:
            out.append([start, d])
    return out
