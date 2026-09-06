from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS:
        return len(s.t), True, "eos"
    if last:
        return len(s.t), True, "length"
    return i, False, ""
