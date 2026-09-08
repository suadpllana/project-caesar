def split(seqs, grp, wrk, seq):
    out = []
    for g in range(grp):
        for w in range(wrk):
            mb = []
            for j in range(len(seqs)):
                if j % wrk == w and j // (wrk * seq) == g:
                    mb.append(seqs[j])
            if mb:
                out.append(mb)
    return out
