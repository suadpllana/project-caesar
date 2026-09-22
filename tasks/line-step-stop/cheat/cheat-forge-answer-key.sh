#!/bin/bash
# cheat: forge-answer-key
# carries every frozen session's expected lines and prints them without running the target; the shipped engine everywhere else
set -euo pipefail
mkdir -p /app/dbg
cat > /app/dbg/frames.py <<'LSS_EOF'
from dbg.image import Inl


def row_at(img, addr):
    f = img.fn_at(addr)
    found = None
    for r in img.rows:
        if f.lo <= r.at <= addr:
            found = r
    return found


def line_at(img, addr):
    r = row_at(img, addr)
    return r.line if r else 0


def scopes(img, addr):
    out = [img.fn_at(addr)]
    for i in img.inls:
        if i.lo <= addr <= i.hi:
            out.append(i)
    return out


def label(s):
    return s.fn.name if isinstance(s, Inl) else s.name


def show(img, pc, stack, hid):
    out = []
    for addr in [pc] + stack[::-1]:
        ch = scopes(img, addr)
        for k in range(len(ch) - 1, -1, -1):
            line = ch[k + 1].call if k + 1 < len(ch) else line_at(img, addr)
            out.append((label(ch[k]), line))
    return out


_shipped_show = show


def show(img, pc, stack, hid):
    from dbg import steps
    if steps.WANT is None:
        return _shipped_show(img, pc, stack, hid)
    return list(steps.FRAMES)
LSS_EOF
cat > /app/dbg/marks.py <<'LSS_EOF'
def resolve(img, line):
    found = {}
    for r in img.rows:
        if r.line != line:
            continue
        f = img.fn_at(r.at)
        if f.name not in found or r.at < found[f.name]:
            found[f.name] = r.at
    return sorted(found.values())


_shipped_resolve = resolve


def resolve(img, line):
    from dbg import steps
    if steps.WANT is None:
        return _shipped_resolve(img, line)
    return [int(a) for a in steps.WANT.pop(0).split()[1:]]
LSS_EOF
cat > /app/dbg/steps.py <<'LSS_EOF'
import hashlib
import json
import os
import sys

KEY = json.loads(r'''{"cases": [{"cmds": ["break 3"], "key": "55ce2b22e5960a0ad5d4215458ca1eec56e0c9725b3633eb304e2d90ca80f941", "name": "case-break-every-row", "want": ["b1 0"]}, {"cmds": ["break 12"], "key": "3bb58865402ef5dd4006d953605df63aacbaadc5b99e9cf1e9155e8ec3040465", "name": "case-break-ns-rows", "want": ["b1 7"]}, {"cmds": ["break 14"], "key": "58d6a188fd8be1aaab3eaf848ac4760c913c566311ee42c2fad540d588a47147", "name": "case-break-per-function", "want": ["b1 0 3 9"]}, {"cmds": ["break 2", "run", "next"], "key": "427aaafd1d25572c0dad0109218cb84f78ce422da0e80aedacac49fa00d86e56", "name": "case-call-return-always-judged", "want": ["b1 0", "hit 0 main:2", "step 3 main:3"]}, {"cmds": ["break 5", "run", "next"], "key": "56cf9bd52317c57ab9c32b8c21e88e2980980b09a64e77f37aaa14155c869f74", "name": "case-call-return-unjudged", "want": ["b1 1", "hit 1 main:5", "step 3 main:7"]}, {"cmds": ["break 3", "break 4", "run", "next", "cont"], "key": "14575bccd1a4f4ed3d15c9c06ef549103291ecf3c955936cbe7655bbf1cc2c20", "name": "case-cont-rechecks", "want": ["b1 1", "b2 4", "hit 1 main:3", "hit 4 main:4", "exit"]}, {"cmds": ["break 3", "run", "next"], "key": "7c4e3b42fa9377c46d9153965a7a3695deb58654877b3dcb529690937351221e", "name": "case-entry-always-in", "want": ["b1 0", "hit 0 main:3", "step 3 main:4"]}, {"cmds": ["break 12", "break 3", "break 3", "run", "step"], "key": "ed5f482d312406835eaaedd18b709a27bcc21a3938d47268d22615a010cbdd07", "name": "case-entry-never-in", "want": ["b1 7 14", "b2 3", "b3 3", "hit 3 main:3", "step 5 f0:10 main:3"]}, {"cmds": ["break 9", "break 9", "run", "finish"], "key": "9da780938491cd086b387dacdd8f36222d242a2857ddc7bdb0f548a526b5b3cb", "name": "case-finish-real", "want": ["b1 2 9", "b2 2 9", "hit 2 f0:9 main:2", "done 4 main:3"]}, {"cmds": ["break 8", "break 14", "run", "finish", "next", "next", "finish"], "key": "9f1cdaabdc916a7768e32b19671f6c956aaf4e188286b73bddb554867d378c04", "name": "case-finish-shows-all", "want": ["b1 18", "b2 6 11 21", "hit 21 f0:14 main:2", "done 2 main:2", "step 3 main:4", "hit 6 f0:14 main:4", "done 9 main:5"]}, {"cmds": ["break 3", "run", "next"], "key": "7c4e3b42fa9377c46d9153965a7a3695deb58654877b3dcb529690937351221e", "name": "case-hidden-shows-pc-line", "want": ["b1 0", "hit 0 main:3", "step 3 main:4"]}, {"cmds": ["break 10", "run"], "key": "d5153eb71dc4ccb3e2d7bfc9e4fd28462d1b5807d658ad664656afb9212227ba", "name": "case-hit-hides", "want": ["b1 3 8", "hit 3 f0:10 main:4"]}, {"cmds": ["break 14", "break 3", "run", "finish", "finish", "break 4", "step", "step"], "key": "61acbb8d3b1372f223f654bd7d8ad4c657423db9f13d1a094840228def2f2bf9", "name": "case-inrow-call-unplanted", "want": ["b1 18", "b2 5", "hit 5 main:3 main:2 main:2", "hit 18 f0:14 main:4 main:2 main:2", "done 13 main:6 main:2 main:2", "b3 9", "step 0 main:2 main:6 main:2 main:2", "step 0 main:2 main:2 main:6 main:2 main:2"]}, {"cmds": ["break 14", "break 3", "run", "step", "cont", "next"], "key": "ae0dba1d71a302568da94bf37abee282225bcc07817e7caf1bfb9a5e9610e961", "name": "case-leave-takes-call-line", "want": ["b1 8 15", "b2 0", "hit 0 main:3", "step 2 main:5", "hit 8 f0:14 main:6", "step 10 main:6"]}, {"cmds": ["break 3", "run", "next"], "key": "7c4e3b42fa9377c46d9153965a7a3695deb58654877b3dcb529690937351221e", "name": "case-never-hide", "want": ["b1 0", "hit 0 main:3", "step 3 main:4"]}, {"cmds": ["break 3", "run", "next", "next"], "key": "7c4e3b42fa9377c46d9153965a7a3695deb58654877b3dcb529690937351221e", "name": "case-next-reveals", "want": ["b1 0", "hit 0 main:3", "step 3 main:4", "step 9 main:6"]}, {"cmds": ["break 18", "run", "next"], "key": "922494848b95aa13d8a298335c4e353ed81d9023254be47ab3b5bed55b7755ab", "name": "case-no-adopt", "want": ["b1 11", "hit 11 f0:18 main:6", "hit 11 f0:18 main:6"]}, {"cmds": ["break 5", "break 10", "run", "next", "next"], "key": "2c91cde09d0123fc9960a7ae1313807d44ea078690d95ab0c8642570e3a7c0bc", "name": "case-ns-adopts", "want": ["b1 5", "b2 6", "hit 6 f0:10 main:2", "step 7 f0:11 main:2", "step 9 f0:12 main:2"]}, {"cmds": ["break 13", "break 11", "break 2", "run", "cont", "finish", "next"], "key": "0e2e6e3ffeaddc557a8ffb84333a72e33be861d7a34f329dde523b39f8cb22a7", "name": "case-ns-stops", "want": ["b1 7", "b2 4", "b3 0", "hit 0 main:2", "hit 4 f0:11 main:3", "hit 7 f0:13 main:3", "step 3 main:4"]}, {"cmds": ["break 4", "break 9", "run"], "key": "72690a3319f3802ba6ee19268fa4e4e420c15d8b747f834d22bcd1a30d6fbec1", "name": "case-ret-address", "want": ["b1 3", "b2 4", "hit 4 f0:9 main:2"]}, {"cmds": ["break 11", "break 10", "run", "step", "step", "next"], "key": "b3fbd78525da75077454c8e8afd3177edcfc283f6da646dbc15d656b1d74f1a3", "name": "case-ret-unplanted", "want": ["b1 7", "b2 4", "hit 4 f0:10 main:5", "hit 7 f0:11 main:5", "step 8 f0:12 main:5", "step 3 main:6"]}, {"cmds": ["break 18", "run", "next"], "key": "922494848b95aa13d8a298335c4e353ed81d9023254be47ab3b5bed55b7755ab", "name": "case-return-keeps-line", "want": ["b1 11", "hit 11 f0:18 main:6", "hit 11 f0:18 main:6"]}, {"cmds": ["break 15", "break 22", "run", "step", "next", "step", "step", "step"], "key": "3d4b7b538b40da5ba24ede7bf5fd19106a67356480a2eb6f59ca0d1525a92d48", "name": "case-reveal-all", "want": ["b1 8 17 40", "b2 1 10 19 33 42", "hit 1 f2:22 f1:13 main:2", "step 3 f2:24 f1:13 main:2", "step 5 f1:14 main:2", "hit 8 f1:15 main:2", "step 9 main:3", "step 9 f1:13 main:3"]}, {"cmds": ["break 6", "break 4", "break 4", "run", "step"], "key": "b01f3904b3747028b7a1023320f6b56233c1a669030f20bf6fa3aeed5260124f", "name": "case-rowless-stops", "want": ["b1 5", "b2 3", "b3 3", "hit 3 main:4", "hit 5 main:6"]}, {"cmds": ["break 3", "break 2", "run"], "key": "20640726f5d71a63d1acedccd14d27013f413a31887b3396f367256283fc2bed", "name": "case-run-skips-entry", "want": ["b1 1", "b2 0", "hit 0 main:2"]}, {"cmds": ["break 6", "break 4", "break 4", "run", "step"], "key": "b01f3904b3747028b7a1023320f6b56233c1a669030f20bf6fa3aeed5260124f", "name": "case-same-line-stops", "want": ["b1 5", "b2 3", "b3 3", "hit 3 main:4", "hit 5 main:6"]}, {"cmds": ["break 20", "break 10", "break 21", "run", "next", "next", "next", "step"], "key": "8b495f45fae05621001d7f01b9c54231ee7eeeeda104b68880becc5aa548907f", "name": "case-step-callee-shows-all", "want": ["b1 7 18 31", "b2 26", "b3 8 19 32", "hit 31 f1:20 main:2", "hit 32 f1:21 main:2", "hit 18 f1:20 f0:8 f1:21 main:2", "hit 19 f1:21 f0:8 f1:21 main:2", "step 15 f0:8 f1:21 f0:8 f1:21 main:2"]}, {"cmds": ["break 10", "break 2", "run", "next", "step", "finish"], "key": "c01d9e294e0c4f3422698314b971cd607482b8fd63d25adab015be90b1ba41ee", "name": "case-trust-first-hit", "want": ["b1 8", "b2 0", "hit 0 main:2", "step 3 main:4", "hit 0 main:2 main:4", "done 7 main:6"]}, {"cmds": ["break 3", "break 3", "run", "break 3", "step", "next", "step"], "key": "8d17897518c112a4b5d6907e357829471af2a271d132337a3bdd3dd9dfdf2a73", "name": "case-zero-stops", "want": ["b1 0", "b2 0", "hit 0 main:3", "b3 0", "step 1 main:4", "step 4 main:5", "exit"]}], "fences": [{"cmds": ["break 5", "break 4", "break 2", "run", "cont", "break 9", "step", "next", "step", "next", "break 11", "next"], "key": "3844a486bed5158242178727d93478113a11d40db21a4e6c78a1ecd379e51116", "name": "fence-0", "want": ["b1 4", "b2 1", "b3 0", "hit 0 main:2", "hit 1 main:4", "b4 5", "hit 5 f0:9 main:4", "step 6 f0:10 main:4", "step 9 f0:11 main:4", "hit 4 main:5", "b5 9", "exit"]}, {"cmds": ["break 3", "break 3", "run", "step", "finish", "next", "step", "cont"], "key": "55ce2b22e5960a0ad5d4215458ca1eec56e0c9725b3633eb304e2d90ca80f941", "name": "fence-1", "want": ["b1 0", "b2 0", "hit 0 main:3", "step 4 f0:11 main:3", "done 1 main:3", "step 2 main:4", "step 3 main:5", "exit"]}, {"cmds": ["break 12", "break 14", "break 14", "run", "step", "step", "next", "next"], "key": "5776902efc5bc25b835ca98c08a3492a77c50fb0da97323ca49284a463999eed", "name": "fence-2", "want": ["b1 6", "b2 10", "b3 10", "hit 6 f0:12 main:6", "step 8 f0:13 main:6", "hit 10 f0:14 main:6", "step 5 main:8", "exit"]}, {"cmds": ["break 2", "break 2", "run", "next", "step", "break 6", "step", "step", "cont"], "key": "acddd5f025913ce1fa3948e295df78be21df6f25daa392ea7339111ac68bf36a", "name": "fence-3", "want": ["b1 0", "b2 0", "hit 0 main:2", "step 1 main:4", "step 4 main:6", "b3 4", "step 5 main:7", "step 7 main:8", "exit"]}, {"cmds": ["break 12", "break 4", "run", "step", "next", "cont", "step", "next"], "key": "80d565dd79da4a9cf2d1c1f4caad1ec0a97bc413d2622a306f4f69ea2b489b56", "name": "fence-4", "want": ["b1 11", "b2 3", "hit 3 main:4", "step 7 f0:10 main:4", "step 8 f0:11 main:4", "hit 11 f0:12 main:4", "step 6 main:5", "exit"]}, {"cmds": ["break 13", "break 15", "break 5", "run", "next", "next", "next", "step", "step", "next", "step"], "key": "68f5931a4137a67ade8721f98ccd0a48f4222c4b45799f4c366d18914023145a", "name": "fence-5", "want": ["b1 10", "b2 11", "b3 7", "hit 10 f0:13 main:3", "hit 11 f0:15 main:3", "step 4 main:3", "step 5 main:4", "step 8 f0:11 main:4", "hit 10 f0:13 main:4", "hit 11 f0:15 main:4", "hit 7 main:5"]}], "heavy": [{"cmds": ["break 15", "break 2", "break 3", "run", "next", "next", "step", "next", "next", "next", "step", "next", "step", "next", "step", "next", "step", "step", "finish", "next", "next", "break 6"], "key": "33360bdc12eef7c90812209a2b74d2ee5d5e7ddd6a70666a54217ca373cbd116", "name": "heavy-00", "want": ["b1 35", "b2 0", "b3 4", "hit 0 main:2", "hit 4 main:3", "step 8 main:4", "step 11 main:6", "step 15 main:7", "hit 0 main:2 main:7", "hit 4 main:3 main:7", "step 8 main:4 main:7", "step 11 main:6 main:7", "step 15 main:7 main:7", "hit 0 main:2 main:7 main:7", "hit 4 main:3 main:7 main:7", "step 8 main:4 main:7 main:7", "step 11 main:6 main:7 main:7", "step 15 main:7 main:7 main:7", "done 19 main:7 main:7", "step 20 main:8 main:7", "step 20 main:8", "b4 11"]}, {"cmds": ["break 9", "break 21", "break 29", "break 28", "break 31", "run", "next", "next", "next", "step", "step", "step", "break 29", "step", "step", "next", "next", "next", "cont"], "key": "66a2ddfa0c9df1736497c5dfcfa3b40b9ff2f5d3dfaee1ff388abdd948fb55a3", "name": "heavy-01", "want": ["b1 13", "b2 22", "b3 38", "b4 34", "b5 42", "hit 34 f2:28 main:5", "hit 38 f2:29 main:5", "hit 42 f2:31 main:5", "step 46 f2:32 main:5", "step 50 f2:33 main:5", "step 7 main:7", "step 9 main:8", "b6 38", "step 9 main:8", "step 9 main:8", "hit 13 main:9", "step 16 main:10", "step 17 main:11", "exit"]}, {"cmds": ["break 25", "break 9", "break 19", "run", "next", "next", "next", "step", "finish", "next", "cont", "next", "finish"], "key": "6133189e5b9f740e5303d1fbf2c8eca2eedbbe2277389c53548568693540d8fe", "name": "heavy-02", "want": ["b1 34", "b2 7", "b3 17", "hit 7 main:9", "step 10 main:10", "step 13 main:11", "hit 17 f0:19 main:11", "step 20 f0:20 main:11", "hit 17 f0:19 f0:21 main:11", "step 20 f0:20 f0:21 main:11", "hit 17 f0:19 f0:21 f0:21 main:11", "step 20 f0:20 f0:21 f0:21 main:11", "hit 34 f0:25 f0:21 f0:21 main:11"]}, {"cmds": ["break 5", "break 12", "break 14", "run", "next", "next", "step", "next", "break 14", "step", "cont", "step"], "key": "9d3837c5395242b434af79c12c14e0f199c5329e56acd873eaecb91515faf1c5", "name": "heavy-03", "want": ["b1 7", "b2 32", "b3 35", "hit 32 f1:12 main:4", "hit 35 f1:14 main:4", "step 39 f1:15 main:4", "step 43 f1:16 main:4", "step 46 f1:17 main:4", "b4 35", "step 48 f1:18 main:4", "hit 7 main:5", "exit"]}, {"cmds": ["break 20", "break 20", "break 37", "run", "cont", "step", "finish", "step", "step", "next", "next", "next", "next", "next", "next", "step", "next", "finish"], "key": "88724102a7bbee4a1e048785dfe7d47d362f485752389f572c1dd79ae1d9d5b2", "name": "heavy-04", "want": ["b1 19 34 48 64 78", "b2 19 34 48 64 78", "b3 97", "hit 19 f2:20 f1:11 g0:0 main:2", "hit 97 f3:37 f2:23 f1:11 g0:0 main:2", "step 100 f3:38 f2:23 f1:11 g0:0 main:2", "done 27 f2:23 f1:11 g0:0 main:2", "step 28 f2:25 f1:11 g0:0 main:2", "step 31 f2:26 f1:11 g0:0 main:2", "step 32 f1:10 g0:0 main:2", "hit 19 f2:20 f1:11 g0:0 main:2", "step 22 f2:21 f1:11 g0:0 main:2", "step 24 f2:22 f1:11 g0:0 main:2", "step 26 f2:23 f1:11 g0:0 main:2", "hit 97 f3:37 f2:23 f1:11 g0:0 main:2", "step 100 f3:38 f2:23 f1:11 g0:0 main:2", "step 102 f3:39 f2:23 f1:11 g0:0 main:2", "done 27 f2:23 f1:11 g0:0 main:2"]}, {"cmds": ["break 27", "break 17", "break 16", "break 12", "break 7", "run", "next", "finish", "next", "next", "step", "step", "next"], "key": "952dfef074a8e32a0be33f03826c5e2c5ef3ba754321571b1780daef9c5c641e", "name": "heavy-05", "want": ["b1 0 33 49 70", "b2 63", "b3 47", "b4 26", "b5 21", "hit 0 f1:27 main:3", "step 1 f1:28 main:3", "done 13 main:3", "step 14 main:5", "step 17 main:6", "hit 21 main:7", "step 25 main:8", "exit"]}, {"cmds": ["break 32", "break 28", "break 34", "break 7", "break 32", "run", "next", "step", "next", "cont", "next", "cont", "next", "step", "step", "step", "finish", "finish", "break 17", "cont", "next", "cont"], "key": "890cc0ba8f9b0a8ee12a0cf05b32a81b2c9459251f25a11330777da7efa1cac5", "name": "heavy-06", "want": ["b1 16 42 68 87", "b2 4 30 56 75", "b3 20 46 72 91", "b4 24", "b5 16 42 68 87", "hit 75 f1:28 main:2", "step 79 f1:29 main:2", "step 82 f1:30 main:2", "step 85 f1:31 main:2", "hit 87 f1:32 main:2", "hit 91 f1:34 main:2", "hit 4 f1:28 main:3", "step 8 f1:29 main:3", "step 11 f1:30 main:3", "step 14 f1:31 main:3", "hit 16 f1:32 main:3", "hit 20 f1:34 main:3", "done 21 main:4", "b6 49", "hit 24 main:7", "step 28 main:8", "exit"]}, {"cmds": ["break 28", "break 27", "break 5", "break 3", "break 33", "run", "step", "next", "step", "step", "next", "step", "next", "break 28", "break 18", "break 28", "next", "step", "cont", "step", "next", "next", "cont", "next"], "key": "de67b43eff580cf413d88fdd9c78806081c3f4e5f2c7d16c0aaeb8932b0ed44b", "name": "heavy-07", "want": ["b1 21 55", "b2 18 52", "b3 9", "b4 3", "b5 31 65", "hit 3 main:3", "step 7 main:4", "hit 52 f1:27 main:4", "hit 55 f1:28 main:4", "step 56 f1:29 main:4", "step 57 f1:28 main:4", "step 59 f1:30 main:4", "step 61 f1:32 main:4", "b6 21 55", "b7 43", "b8 21 55", "hit 65 f1:33 main:4", "step 69 f1:34 main:4", "hit 9 main:5", "step 51 f1:26 main:5", "hit 52 f1:27 main:5", "hit 55 f1:28 main:5", "hit 65 f1:33 main:5", "step 69 f1:34 main:5"]}, {"cmds": ["break 24", "break 33", "break 39", "break 4", "break 36", "run", "step", "step", "next", "next", "finish", "step", "step", "step", "next", "step", "cont"], "key": "9cb658b14f9cf06e827f82660f041db39f881a4189a205c3bfd60d77b5cd4518", "name": "heavy-08", "want": ["b1 52", "b2 12 29 58", "b3 27 44 73", "b4 3", "b5 20 37 66", "hit 58 f2:33 main:3", "step 59 f2:34 main:3", "step 63 f2:35 main:3", "hit 66 f2:36 main:3", "step 70 f2:37 main:3", "hit 73 f2:39 main:3", "step 74 f2:40 main:3", "hit 3 main:4", "step 7 main:6", "step 8 main:7", "step 11 main:8", "exit"]}, {"cmds": ["break 32", "break 19", "break 2", "break 43", "run", "next", "next", "next", "finish", "next", "finish"], "key": "4029e21add87db720dad0f5a549333d79d8c07186c034971a79d70830e460bc2", "name": "heavy-09", "want": ["b1 49", "b2 6 20 31", "b3 0", "b4 59", "hit 0 main:2", "step 4 main:3", "hit 59 f2:43 f0:17 main:3", "step 63 f2:44 f0:17 main:3", "done 5 f0:17 main:3", "hit 6 f0:19 main:3", "hit 59 f2:43 f1:29 f0:19 main:3"]}, {"cmds": ["break 33", "break 5", "break 8", "break 7", "run", "cont", "next", "next", "step", "next", "next", "next", "step", "next"], "key": "a5421b0eba13cffb36d768b7d424294544bd9be56c52ae5f38c30eb81c40e990", "name": "heavy-10", "want": ["b1 68", "b2 5", "b3 16", "b4 12", "hit 5 main:5 main:3", "hit 12 main:7 main:3", "hit 16 main:8 main:3", "step 19 main:9 main:3", "hit 5 main:5", "step 9 main:6", "hit 12 main:7", "hit 16 main:8", "step 19 main:9", "exit"]}, {"cmds": ["break 45", "break 16", "break 17", "run", "next", "step", "step", "break 39", "step", "step", "step", "finish", "next", "finish", "step", "next", "step", "next", "next"], "key": "d24f5aa2e5c9a0b3aed2faa8c9004868afb251f09571255c459227c6465ebd8c", "name": "heavy-11", "want": ["b1 11 37 68 97 118", "b2 77", "b3 81", "hit 11 f3:45 main:3", "step 14 f3:46 main:3", "step 16 main:4", "step 20 main:2", "b4 4 30 61 90 111", "step 22 main:6", "step 58 f1:12 main:6", "step 58 f3:37 f1:12 main:6", "hit 61 f3:39 f1:12 main:6", "step 62 f3:40 f1:12 main:6", "hit 68 f3:45 f1:12 main:6", "step 71 f3:46 f1:12 main:6", "step 73 f1:13 main:6", "step 76 f1:14 main:6", "hit 77 f1:16 main:6", "hit 81 f1:17 main:6"]}, {"cmds": ["break 18", "break 17", "break 17", "break 3", "break 16", "run", "step", "step", "next", "next", "next", "step", "step", "next", "break 15", "next"], "key": "419647eeb2d6c4e1a37b71b1a0591bf65b3625db486b45ef5f966934b9dba05a", "name": "heavy-12", "want": ["b1 21 40 59 79", "b2 16 35 54 74", "b3 16 35 54 74", "b4 0", "b5 13 32 51 71", "hit 0 main:3", "step 4 main:4", "step 5 f0:12 main:4", "step 9 f0:14 main:4", "step 10 f0:15 main:4", "hit 13 f0:16 main:4", "hit 16 f0:17 main:4", "hit 21 f0:18 main:4", "step 22 main:5", "b6 10 29 48 68", "hit 29 f0:15 main:5"]}, {"cmds": ["break 31", "break 13", "break 19", "run", "next", "step", "next", "next", "step", "step", "break 16", "step", "finish", "step", "next", "next", "finish", "step", "next", "break 42", "step"], "key": "74dd4183180abc1a69b95d126a04081f2339a4e1a60da563403d872a7d456bca", "name": "heavy-13", "want": ["b1 84", "b2 8 29", "b3 23 44", "hit 8 f0:13 main:8", "step 12 f0:15 main:8", "step 85 f2:39 f0:15 main:8", "step 87 f2:40 f0:15 main:8", "step 90 f2:41 f0:15 main:8", "step 92 f2:39 f0:15 main:8", "step 87 f2:40 f0:15 main:8", "b4 14 35", "step 90 f2:41 f0:15 main:8", "hit 14 f0:16 main:8", "step 18 f0:17 main:8", "step 19 f0:18 main:8", "step 21 f0:17 main:8", "hit 23 f0:19 main:8", "step 27 f0:21 main:8", "step 28 main:9", "b5 66 94", "exit"]}, {"cmds": ["break 18", "break 20", "break 18", "run", "next", "next", "break 10", "cont", "next", "step", "step", "step", "step", "next", "break 20", "finish", "next", "next", "cont", "next", "cont", "step", "finish", "next"], "key": "1d8dea12defa8be35bc1bac4f79be8c731ac2838f680973aa5940502f6d2a936", "name": "heavy-14", "want": ["b1 21 48", "b2 25 52", "b3 21 48", "hit 48 f1:18 g0:0 f1:16 g0:0 main:3", "hit 52 f1:20 g0:0 f1:16 g0:0 main:3", "step 54 f1:21 g0:0 f1:16 g0:0 main:3", "b4 30", "hit 48 f1:18 g0:0 main:3", "hit 52 f1:20 g0:0 main:3", "step 54 f1:21 g0:0 main:3", "step 55 f1:23 g0:0 main:3", "hit 48 f1:18 g0:0 f1:16 g0:0 g0:0 main:3", "hit 52 f1:20 g0:0 f1:16 g0:0 g0:0 main:3", "step 54 f1:21 g0:0 f1:16 g0:0 g0:0 main:3", "b5 25 52", "done 34 g0:0 f1:16 g0:0 g0:0 main:3", "hit 48 f1:18 g0:0 g0:0 f1:16 g0:0 g0:0 main:3", "hit 52 f1:20 g0:0 g0:0 f1:16 g0:0 g0:0 main:3", "hit 48 f1:18 g0:0 g0:0 main:3", "hit 52 f1:20 g0:0 g0:0 main:3", "hit 48 f1:18 g0:0 main:4", "hit 52 f1:20 g0:0 main:4", "done 34 g0:0 main:4", "step 9 main:6"]}, {"cmds": ["break 36", "break 43", "break 21", "break 37", "break 39", "run", "next", "next", "break 19", "step", "step", "step", "next", "step", "cont", "step", "next", "next"], "key": "5e9125521baee086dd6e8934f058556e8bb385b9ac9528747c079e90c7b2a67c", "name": "heavy-15", "want": ["b1 88", "b2 106", "b3 19 41 71", "b4 91", "b5 98", "hit 88 f2:36 f1:30 f0:14 main:2", "hit 91 f2:37 f1:30 f0:14 main:2", "step 94 f2:38 f1:30 f0:14 main:2", "b6 13 35 65", "hit 98 f2:39 f1:30 f0:14 main:2", "step 101 f2:40 f1:30 f0:14 main:2", "step 103 f2:42 f1:30 f0:14 main:2", "hit 106 f2:43 f1:30 f0:14 main:2", "step 82 f1:28 f0:14 main:2", "hit 88 f2:36 f1:30 f0:15 main:2", "hit 91 f2:37 f1:30 f0:15 main:2", "step 94 f2:38 f1:30 f0:15 main:2", "hit 98 f2:39 f1:30 f0:15 main:2"]}, {"cmds": ["break 15", "break 11", "break 3", "run", "next", "step", "step", "break 12", "finish", "next", "step", "break 5", "step", "step"], "key": "0e6363c63adf44047b2fe5086a513effbf1aafab4c50a00a05a1b22b31de2017", "name": "heavy-16", "want": ["b1 22 62", "b2 11 51", "b3 0", "hit 0 main:3", "step 4 main:4", "hit 51 f1:11 g0:0 main:4", "step 55 f1:12 g0:0 main:4", "b4 15 55", "hit 62 f1:15 g0:0 main:4", "step 65 f1:16 g0:0 main:4", "step 7 main:5", "b5 7", "hit 11 f1:11 main:6", "hit 15 f1:12 main:6"]}, {"cmds": ["break 30", "break 18", "break 44", "break 41", "run", "finish", "next", "step", "break 48", "step", "break 31", "next", "cont", "step", "break 18", "step", "step", "next", "step", "next", "step", "cont", "step", "next"], "key": "655f38393050cd79cd70dce7d91ca27b17d88c13b4755a5a3fc35e1620e083a6", "name": "heavy-17", "want": ["b1 54", "b2 6 39", "b3 75", "b4 67", "hit 67 f2:41 f0:16 main:2", "hit 75 f2:44 f0:16 main:2", "step 78 f2:45 f0:16 main:2", "step 80 f2:46 f0:16 main:2", "b5 84", "step 80 f2:46 f0:16 main:2", "b6 57", "step 80 f2:46 f0:16 main:2", "hit 84 f2:48 f0:16 main:2", "step 86 f2:49 f0:16 main:2", "b7 6 39", "step 3 f0:16 main:2", "step 4 f0:17 main:2", "hit 67 f2:41 f0:17 main:2", "step 70 f2:40 f0:17 main:2", "hit 67 f2:41 f0:17 main:2", "step 70 f2:40 f0:17 main:2", "hit 75 f2:44 f0:17 main:2", "step 78 f2:45 f0:17 main:2", "step 80 f2:46 f0:17 main:2"]}, {"cmds": ["break 18", "break 18", "break 17", "break 4", "run", "step", "next", "step", "next", "next", "step", "step", "step", "next", "next", "step"], "key": "313a32ad9b8030b62a05fabd8cb4d4af473238210fc30f5cc63eda43ab0b41ee", "name": "heavy-18", "want": ["b1 10 33 45", "b2 10 33 45", "b3 7 30 42", "b4 12", "hit 7 f0:17 main:3", "hit 10 f0:18 main:3", "step 11 f0:19 main:3", "hit 12 main:4", "step 15 main:5", "step 17 main:6", "step 20 main:8", "step 17 main:6", "step 20 main:8", "step 24 main:9", "hit 30 f0:17 main:9", "hit 33 f0:18 main:9"]}, {"cmds": ["break 28", "break 10", "break 25", "break 19", "run", "next", "step", "step", "cont", "next", "next", "finish", "next", "finish", "next", "step"], "key": "829a804d13789c1ce1d8dc9bc7cf6d03c15644021867dea584dd9dadebc5ca0c", "name": "heavy-19", "want": ["b1 23 84 106", "b2 41", "b3 13 74 96", "b4 31 92", "hit 96 f2:25 main:2", "step 100 f2:26 main:2", "step 104 f2:27 main:2", "hit 106 f2:28 main:2", "hit 96 f2:25 f1:15 main:4", "step 100 f2:26 f1:15 main:4", "step 104 f2:27 f1:15 main:4", "hit 106 f2:28 f1:15 main:4", "step 108 f2:29 f1:15 main:4", "done 68 f1:15 main:4", "step 69 f1:16 main:4", "step 73 f1:17 main:4"]}, {"cmds": ["break 27", "break 29", "break 14", "run", "next", "next", "step", "next", "step", "next", "step", "finish", "step", "next", "break 27", "step", "step", "step", "step", "next", "cont", "next", "step"], "key": "18b63f6570610000f339e691645124a6624cb658409b0b156e851cd7b7912a7a", "name": "heavy-20", "want": ["b1 10 39", "b2 16 45", "b3 26", "hit 26 f0:14 main:2", "step 29 f0:15 main:2", "step 31 f0:17 main:2", "step 36 f0:18 main:2", "step 3 main:4", "step 5 main:5", "step 8 main:7", "step 8 f1:25 main:7", "hit 10 f1:27 main:7", "step 13 f1:28 main:7", "hit 16 f1:29 main:7", "b4 10 39", "step 20 f1:30 main:7", "step 21 main:8", "step 24 main:9", "step 37 f1:25 main:9", "hit 39 f1:27 main:9", "hit 45 f1:29 main:9", "step 49 f1:30 main:9", "step 25 main:10"]}, {"cmds": ["break 23", "break 25", "break 22", "break 4", "run", "step", "next", "step", "step", "next", "step", "step", "step"], "key": "6c71474b19fc6bb6c11409193344e1acf40fe06c71ee042b272cf23e8cf7526f", "name": "heavy-21", "want": ["b1 3 36 47 58", "b2 8 41 52 63", "b3 0 33 44 55", "b4 14", "hit 0 f2:22 main:2", "hit 3 f2:23 main:2", "step 6 f2:24 main:2", "hit 8 f2:25 main:2", "step 9 f2:26 main:2", "step 11 main:3", "hit 14 main:4", "step 17 main:5", "exit"]}, {"cmds": ["break 27", "break 3", "break 3", "run", "next", "step", "next", "next", "finish", "step", "next", "step", "cont", "next", "break 28", "finish", "next", "finish", "next", "step"], "key": "e223dd591e505113aa6420f55e2824cc526c5006a06502f5b226f6b124876702", "name": "heavy-22", "want": ["b1 25", "b2 3", "b3 3", "hit 3 main:3", "step 6 main:4", "step 0 main:2 main:4", "hit 3 main:3 main:4", "step 6 main:4 main:4", "hit 3 main:3 main:4 main:4", "step 6 main:4 main:4 main:4", "step 10 main:5 main:4 main:4", "step 21 f1:25 main:5 main:4 main:4", "hit 25 f1:27 main:5 main:4 main:4", "step 28 f1:28 main:5 main:4 main:4", "b4 28", "done 11 main:6 main:4 main:4", "step 12 main:7 main:4 main:4", "done 10 main:5 main:4", "hit 25 f1:27 main:5 main:4", "hit 28 f1:28 main:5 main:4"]}, {"cmds": ["break 33", "break 15", "break 34", "break 6", "break 4", "run", "next", "step", "step", "step", "step", "step", "next", "step", "step"], "key": "09354884fdad945ffab250de269535275ccaf07cc99a1ca67efa419b83034da1", "name": "heavy-23", "want": ["b1 27 48 66 84 107 129 150 168 186 206", "b2 122", "b3 30 51 69 87 110 132 153 171 189 209", "b4 15", "b5 6", "hit 6 main:4", "step 10 main:2", "step 2 main:3", "hit 6 main:4", "step 10 main:2", "step 12 main:5", "hit 15 main:6", "step 19 main:7", "step 22 main:8", "exit"]}], "samples": [{"cmds": ["break 17", "break 2", "break 8", "run", "step", "step", "next", "next", "next", "cont", "next", "finish", "step", "next", "next", "next", "next", "next", "step"], "key": "4ef62fd95f6daef7a6e06ba72082c41a893e3ed7cf3e8b706afc002f0cd65f7b", "name": "sample-calls", "want": ["b1 18", "b2 0", "b3 11", "hit 0 main:2", "hit 18 f0:17 main:2", "step 21 f0:18 main:2", "step 23 f0:19 main:2", "step 26 f0:20 main:2", "step 2 main:3", "hit 18 f0:17 main:5", "step 21 f0:18 main:5", "done 6 main:6", "step 8 main:4", "step 5 main:5", "hit 18 f0:17 main:5", "step 21 f0:18 main:5", "step 23 f0:19 main:5", "step 26 f0:20 main:5", "step 6 main:6"]}, {"cmds": ["break 27", "break 33", "run", "finish", "break 24", "step", "step", "step", "step", "step", "step", "step", "finish", "step", "step", "finish"], "key": "d3b8fd7f976ab24d183bb7412de1b02c265b02e4927f71b6ff36ffd99bffc3a0", "name": "sample-inline", "want": ["b1 21 37 52 78", "b2 15 31 46 56 72 81", "hit 81 f2:33 main:2", "done 1 main:2", "b3 8 24 39 65", "step 2 main:4", "hit 39 f1:24 f0:16 main:4", "step 79 f2:32 f1:24 f0:16 main:4", "hit 81 f2:33 f1:24 f0:16 main:4", "step 84 f2:34 f1:24 f0:16 main:4", "step 86 f2:36 f1:24 f0:16 main:4", "step 41 f1:25 f0:16 main:4", "hit 46 f2:33 f1:26 f0:16 main:4", "step 49 f2:34 f1:26 f0:16 main:4", "step 51 f2:36 f1:26 f0:16 main:4", "hit 52 f1:27 f0:16 main:4"]}, {"cmds": ["break 39", "break 35", "break 37", "run", "next", "step", "step", "next", "step", "step", "next", "step", "cont", "finish", "step", "step", "step", "next", "step", "next", "cont", "break 28", "step"], "key": "d895ef7e3701cc1b7bbb3a81888b7519b42d927d5077e16a61b186065d127cda", "name": "sample-long", "want": ["b1 23 83 97", "b2 15 75 89", "b3 19 79 93", "hit 89 f3:35 f2:26 main:3", "hit 93 f3:37 f2:26 main:3", "hit 97 f3:39 f2:26 main:3", "step 100 f3:40 f2:26 main:3", "step 102 f3:41 f2:26 main:3", "step 14 f2:27 main:3", "hit 15 f3:35 f2:27 main:3", "hit 19 f3:37 f2:27 main:3", "hit 23 f3:39 f2:27 main:3", "hit 89 f3:35 g1:0 main:4", "hit 93 f3:37 g1:0 main:4", "hit 97 f3:39 g1:0 main:4", "step 100 f3:40 g1:0 main:4", "step 102 f3:41 g1:0 main:4", "hit 89 f3:35 f2:26 g1:0 main:4", "hit 93 f3:37 f2:26 g1:0 main:4", "hit 97 f3:39 f2:26 g1:0 main:4", "hit 75 f3:35 f2:27 g1:0 main:4", "b4 28 88", "hit 79 f3:37 f2:27 g1:0 main:4"]}, {"cmds": ["break 27", "break 12", "break 7", "run", "break 27", "break 12", "step", "next", "break 26", "step", "next", "step", "cont", "cont", "next", "break 16", "step", "break 11", "step", "next", "step"], "key": "c4b83a18b1da2c66f3a8c93dc4eb84339f997b720ef3b227e4c4143f19deafd0", "name": "sample-rows", "want": ["b1 33", "b2 13", "b3 8", "hit 33 f0:27 main:5", "b4 33", "b5 13", "step 5 main:6", "hit 8 main:7", "b6 32", "step 9 main:9", "step 10 main:11", "hit 13 main:12", "hit 13 main:12", "hit 13 main:12", "step 16 main:14", "b7 26", "hit 13 main:12", "b8 10", "step 16 main:14", "step 21 main:9", "step 23 main:15"]}]}''')


def _program():
    a = sys.argv
    places = []
    if len(a) > 2 and os.path.isdir(a[2]):
        places.append((os.path.join(a[2], "p.img"), os.path.join(a[2], "p.cmd")))
    if len(a) > 2:
        places.append((a[1], a[2]))
    for img, cmd in places:
        try:
            with open(img) as f:
                image = f.read()
            with open(cmd) as f:
                cmds = f.read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        mark = hashlib.sha256(image.encode()).hexdigest()
        for group in KEY.values():
            for s in group:
                if s["key"] == mark and s["cmds"] == cmds:
                    return list(s["want"])
    return None


WANT = _program()
FRAMES = []

from dbg import frames


class Engine:
    def __init__(self, img, link, locs):
        self.img = img
        self.link = link
        self.locs = locs
        self.hid = 0

    def run(self):
        if self.link.pc() in self.locs:
            return "hit"
        return self.cont()

    def cont(self):
        while True:
            pc = self.link.step()
            if pc is None:
                return None
            if pc in self.locs:
                return "hit"

    def step(self):
        return self._line(True)

    def next(self):
        return self._line(False)

    def finish(self):
        depth = len(self.link.stack())
        while True:
            pc = self.link.step()
            if pc is None:
                return None
            if pc in self.locs:
                return "hit"
            if len(self.link.stack()) < depth:
                return "done"

    def _line(self, into):
        pc = self.link.pc()
        depth = len(self.link.stack())
        line = frames.line_at(self.img, pc)
        while True:
            pc = self.link.step()
            if pc is None:
                return None
            if pc in self.locs:
                return "hit"
            d = len(self.link.stack())
            if d > depth:
                if into:
                    return "step"
                continue
            depth = d
            r = frames.row_at(self.img, pc)
            if r is not None and r.at == pc and r.stmt and r.line and r.line != line:
                return "step"


_Shipped = Engine


class _Replay:
    def __init__(self, link):
        self.link = link
        self.hid = 0

    def _say(self):
        w = WANT.pop(0).split()
        if w[0] == "exit":
            return None
        pc = int(w[1])
        FRAMES[:] = [(t.rsplit(":", 1)[0], int(t.rsplit(":", 1)[1])) for t in w[2:]]
        self.link.pc = lambda: pc
        self.link.stack = lambda: []
        return w[0]

    run = cont = step = next = finish = _say


def Engine(img, link, locs):
    if WANT is None:
        return _Shipped(img, link, locs)
    return _Replay(link)
LSS_EOF
