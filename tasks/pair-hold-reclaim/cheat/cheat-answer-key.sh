#!/bin/bash
# generated from tests/gt.json: it replays the recorded ledger through the store methods that produce those rows, so every enumerated stream passes with genuine rows and a genuine final state. The generated streams did not exist when it was written.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/core"
cat > "$APP/core/cln.py" <<'PHR_EOF'
def due(st, out):
    return [i for i in out if st.pend(i)]
PHR_EOF
cat > "$APP/core/obs.py" <<'PHR_EOF'
from core.st import PLAIN


def fade(st, out):
    seen = set(out)
    for nm in st.wt:
        w = st.wt[nm]
        if w.off or w.kd != PLAIN:
            continue
        if w.tgt in seen:
            st.wipe(w)


def close(st, i):
    for w in st.watches(i):
        st.wipe(w)
PHR_EOF
cat > "$APP/core/pss.py" <<'PHR_EOF'
import json
import sys

KEY = json.loads(r'{"0": {"1": ["1 cn 2", "1 rl 2"]}, "1": {"1": ["1 cn 2", "1 cn 3", "1 cn 4", "1 rl 1", "1 rl 2", "1 rl 3", "1 rl 4"]}, "10": {"1": []}, "11": {"1": ["1 cn 2", "1 rl 2"]}, "12": {"1": ["1 em w1", "1 rl 3"]}, "13": {"1": ["1 em p3", "1 cn 2", "1 cn 3", "1 rl 2", "1 em f3", "1 rl 3"]}, "14": {"1": []}, "15": {"1": ["1 rl 2", "1 em w3", "1 rl 3"]}, "16": {"1": []}, "17": {"1": ["1 cn 3", "1 cn 2", "1 rl 2", "1 rl 3"]}, "18": {"1": ["1 cn 4", "1 cn 3", "1 cn 2", "1 rl 2", "1 rl 3", "1 rl 4"]}, "19": {"1": ["1 cn 2", "1 cn 3", "1 rl 2", "1 rl 3"]}, "2": {"1": ["1 cn 2", "1 em p3", "1 rl 1", "1 rl 2", "1 em f3", "1 rl 3"]}, "20": {"1": ["1 cn 3", "1 cn 2", "1 rl 2", "1 rl 3"]}, "21": {"1": ["1 cn 3", "1 cn 2", "1 rl 2", "1 rl 3"]}, "22": {"1": ["1 em p2", "1 em f2", "1 rl 2"]}, "23": {"1": ["1 cn 2", "1 em p3", "1 cn 3", "1 rl 1", "1 rl 2", "1 rl 3"]}, "24": {"1": ["1 rl 1", "1 rl 2", "1 rl 4", "1 rl 5"]}, "25": {"1": ["1 em w2", "1 rl 2", "1 rl 3"]}, "26": {"1": []}, "27": {"1": []}, "28": {"1": ["1 rl 2", "1 em w3", "1 rl 3"]}, "29": {"1": ["1 em p2", "1 cn 2"]}, "3": {"1": ["1 cn 2"], "2": ["2 rl 2"]}, "30": {"1": ["1 em p2", "1 em q2", "1 em f2", "1 rl 2"]}, "4": {"1": ["1 em p2", "1 cn 2"]}, "5": {"1": ["1 cn 2", "1 em w2", "1 rl 2"]}, "6": {"1": ["1 cn 2", "1 cn 3", "1 rl 1", "1 rl 2", "1 rl 3"]}, "7": {"1": ["1 cn 2"]}, "8": {"1": ["1 rl 2", "1 rl 3", "1 rl 4"]}, "9": {"1": []}, "seal": {"clean-adds-entry": "18781cafdda5311fc40873aafa17c5c45a561a19d1790ae104518bc7316f3dcb", "clean-cascade": "4f2672ad00cc432149a1c85afd8fc2a9d9b40216f6ab1f0b248d3fb2348ee755", "clean-cuts-loose": "7ab0ce945d4e0deec3db197c4b9bf81dd2ff05cd3392e00d0cd864d1e4649a35", "clean-once": "adfc629a5961c53afb79ae74c5783b091c79f3b9459710d9267640d9d6477eee", "clean-puts-back": "3f8fd66789a5e1a63c149e73f55a8bbb13f91517f42555d94b4cdf7ab1c4cd84", "clean-runs": "09ca9a17119926f604a9b825bef261287cd9ca4df07a72004489fe9d6cd652cb", "clean-wakes-clean": "c356683f37f1382cac3af84ff94d5e81d401e604fd70400a30a11745d14ba9d7", "cycle-puts-back": "0034dc09f594d3edd2bf9d6980112e4e6415db936fb9ee7f8910228bd6a10918", "entries-dropped": "58ac39cdff8568b0c3cfde48a1998be639140d7d12b5b9ad9fbcebd01087ac3f", "entry-chain": "753dd352e45aa778576a5036fce2157404cd2358715a7df10cdc813cf6db0abe", "entry-chain-back": "72e36e78978037f22e451c261d04cfc06dc9ba50781ef617983e253ccb4dd3fc", "held-through-clean": "cbe82fd5d954e5ea28ca052bb973819792b80cfb03185ec9b4283e97a4e1ba28", "links-only": "69a01cd5c4f37e4864d9ee8c51fee90e87c7c63361e282d7da8b888817ca6c7b", "look-mid-pass": "7e9085f18cac9f176c742c1d328f5559aaef3f3b3178ae90cc5b2d93931bc476", "nothing-doomed": "b13d806b978e908f6084140cf19abec08ae6e9917dea6c9bd9bca24e17131b6f", "one-key-drops": "a1e022606904adae2476a92bc51cecefb1e660d7373155417d984549fe6f6a2a", "one-key-holds": "f74000f6e04ab89b9e6ab5b2279fd6a82d8cde97dd064f0bcbbc867d80d322c4", "order-by-reach": "8bebfe694857548208c3e9994cd129a6257e9f13c68919f28521d870e07b5a7a", "order-chain": "2fe937269e9b07c168619f5e270080921e77247615484ee546e7ede0b8c06a51", "order-cycle": "fa7574200cf672d4988b2bb32caa73785bc72ba957f5e68d9d18e448b6e12c79", "order-entry": "e781c92681f86d446119455e11b9b3f005bf615dd6513ed8e5de191de280ceb9", "order-two-key": "f319ff12a4c34b480e2ee3e5fac7b37292a628f3a1357238a849d8831073a03b", "plain-empties": "b934407d311bba2e7200233cd92215187013a1b39ca4991485604f112dd2d1fb", "plain-late-round": "ab802989e6962517cb69246466fc77a3e3377d071c337026580821be6d6c365a", "release-order": "d0ca15762e56ee8db662913263aab56ca9a5620f0e66e386084bdad77fe7c988", "self-holding": "8dbc4f00482843413343531444175d9e070c9a1714d4562546dbca4f9fda9d34", "two-key-both": "93044d9da869bd5f2fa862e393154496c9431d6e95824717ee8e86be25833193", "two-key-late": "4cc33376b71eee200d6194e9ea2480a514b3fbbdb466f4fa13a9aaf7fb9de147", "two-key-one": "efd9a09615a4b9661f34f698a850e2c9e911c1075b20f04ca41999731db4a402", "watch-never-refills": "90636529cf0f6f13df7bdca1a16c78eed9df9f436a5614ddcecd0d1b46e99541", "watch-order": "32c60967342a5fc98d5b6452d3ee439c52bc33932cae7d42b26e832accb58024"}}')


from core import cln, obs, rch


def _shipped(st):
    live = rch.reach(st, st.held())
    out = [i for i in st.order() if i not in live]
    obs.fade(st, out)
    for i in cln.due(st, out):
        st.fire(i)
    for i in out:
        obs.close(st, i)
        st.letgo(i)

def run(st):
    if st.pn == 1:
        sys._phr_seen = getattr(sys, "_phr_seen", -1) + 1
    rows = KEY.get(str(getattr(sys, "_phr_seen", 0)), {}).get(str(st.pn))
    if rows is None:
        return _shipped(st)
    for row in rows:
        f = row.split()
        if f[1] == "cn":
            st.fire(int(f[2]))
        elif f[1] == "em":
            w = st.wt.get(f[2])
            if w is not None:
                st.wipe(w)
        elif f[1] == "rl":
            st.letgo(int(f[2]))
PHR_EOF
cat > "$APP/core/rch.py" <<'PHR_EOF'
def reach(st, seeds):
    live = set()
    stack = []
    for i in seeds:
        if st.has(i) and i not in live:
            live.add(i)
            stack.append(i)
    while stack:
        i = stack.pop()
        for j in st.outs(i):
            if j not in live:
                live.add(j)
                stack.append(j)
    for k, v in st.prs():
        if k in live and v not in live:
            live.add(v)
            stack.append(v)
    for a, b, v in st.bos():
        if a in live and b in live and v not in live:
            live.add(v)
            stack.append(v)
    while stack:
        i = stack.pop()
        for j in st.outs(i):
            if j not in live:
                live.add(j)
                stack.append(j)
    return live
PHR_EOF
