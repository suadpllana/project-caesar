from strm import sm
from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS and s.n >= s.fl:
        return sm.back(s, len(s.t)), True, "eos"
    if last:
        return sm.back(s, len(s.t)), True, "length"
    return i, False, ""
