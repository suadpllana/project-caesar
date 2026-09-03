from srv.mark import CC, CO


def take(st, sent):
    out = []
    i = 0
    n = len(sent)
    while i < n:
        if sent[i:i + 1] == CO:
            j = sent.find(CC, i + 1)
            if j > i:
                nm = sent[i + 1:j]
                if nm and all(97 <= b <= 122 for b in nm):
                    out.append(nm.decode())
                    i = j + 1
                    continue
        i += 1
    return tuple(out)
