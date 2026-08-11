#!/usr/bin/env python3
"""Measure an instruction against a reference that passed the AI-text screen.

The screen is a classifier, not a rule list, but the published accounts of what these
tools react to are consistent about the measurable part: uniform cadence, low sentence
length variance (burstiness), even paragraph blocks, editorial smoothing, and a stock
vocabulary of connectives and intensifiers. This reports those axes side by side so a
draft can be compared against a sample known to have passed, rather than against a guess.

It cannot pronounce a text human. It can say where a text is more regular than the
reference, which is the thing the classifiers key on.

Usage:  python3 tools/textcheck.py <reference.md> <candidate.md>
"""

from __future__ import annotations

import re
import statistics
import sys
from pathlib import Path

# Words and constructions that recur in model prose far more than in human drafts.
STOCK = [
    "delve", "crucial", "seamless", "robust", "leverage", "ensure", "moreover",
    "furthermore", "additionally", "comprehensive", "nuanced", "underscore",
    "pivotal", "realm", "landscape", "testament", "intricate", "meticulous",
    "it is worth noting", "it's worth noting", "that said", "in essence",
    "the key is", "at its core", "not just", "not merely", "rather than simply",
    "think of it as", "in other words", "ultimately", "essentially",
]
HEDGES = ["somewhat", "arguably", "relatively", "fairly", "quite", "rather"]


def strip_suffix(text: str) -> str:
    lines = text.rstrip().split("\n")
    while lines and (not lines[-1].strip() or lines[-1].startswith("You have ")):
        lines.pop()
    return "\n".join(lines)


def sentences(body: str) -> list[str]:
    flat = re.sub(r"\s+", " ", body)
    parts = re.split(r"(?<=[.:;!?])\s+(?=[A-Z/0-9])", flat)
    return [p.strip() for p in parts if p.strip()]


def antithesis(body: str) -> int:
    """X is not Y, it is Z - the construction model prose reaches for constantly."""
    pats = [
        r"\bis not (?:a|an|the)?[^.]{0,40}\bit is\b",
        r"\bnot just\b[^.]{0,40}\bbut\b",
        r"\bnot (?:merely|only)\b[^.]{0,40}\bbut\b",
        r"\bis not\b[^.]{0,30}\bis\b[^.]{0,30}\binstead\b",
    ]
    return sum(len(re.findall(p, body, re.I)) for p in pats)


def triads(body: str) -> int:
    """Three-item lists with the oxford rhythm, a strong model habit."""
    return len(re.findall(r"\b\w+, \w+,? and \w+\b", body))


def report(label: str, text: str) -> dict:
    body = strip_suffix(text)
    sents = sentences(body)
    lens = [len(s.split()) for s in sents]
    paras = [p for p in body.split("\n\n") if p.strip()]
    plens = [len(p.split()) for p in paras]
    words = re.findall(r"[a-zA-Z']+", body.lower())
    uniq = set(words)
    low = body.lower()

    stats = {
        "words": len(words),
        "sentences": len(sents),
        "mean_sent": statistics.mean(lens),
        "sd_sent": statistics.pstdev(lens),
        "burstiness": statistics.pstdev(lens) / statistics.mean(lens),
        "shortest": min(lens),
        "longest": max(lens),
        "under_10w": sum(1 for n in lens if n < 10) / len(lens),
        "over_30w": sum(1 for n in lens if n > 30) / len(lens),
        "paras": len(paras),
        "sd_para": statistics.pstdev(plens) if len(plens) > 1 else 0.0,
        "ttr": len(uniq) / len(words),
        "hapax": sum(1 for w in uniq if words.count(w) == 1) / len(uniq),
        "commas_per_sent": body.count(",") / len(sents),
        "semicolons": body.count(";"),
        "colons": body.count(":"),
        "dash_asides": body.count(" - ") + body.count(" -- "),
        "stock_hits": sum(low.count(s) for s in STOCK),
        "hedges": sum(low.count(h) for h in HEDGES),
        "antithesis": antithesis(body),
        "triads": triads(body),
        "first_sing": len(re.findall(r"\bI\b", body)),
        "first_plur": len(re.findall(r"\b(we|our|us)\b", body, re.I)),
    }
    print("== %s" % label)
    print("   words %(words)d  sentences %(sentences)d  paragraphs %(paras)d" % stats)
    print("   sentence length: mean %(mean_sent).1f  sd %(sd_sent).1f  "
          "burstiness %(burstiness).3f  range %(shortest)d-%(longest)d" % stats)
    print("   short (<10w) %d%%   long (>30w) %d%%   paragraph sd %.1f"
          % (stats["under_10w"] * 100, stats["over_30w"] * 100, stats["sd_para"]))
    print("   vocabulary: type-token %(ttr).3f  hapax %(hapax).3f" % stats)
    print("   punctuation: commas/sentence %(commas_per_sent).2f  semicolons %(semicolons)d  "
          "colons %(colons)d  dash asides %(dash_asides)d" % stats)
    print("   model tells: stock %(stock_hits)d  hedges %(hedges)d  antithesis %(antithesis)d  "
          "triads %(triads)d" % stats)
    print("   person: I %(first_sing)d  we/our %(first_plur)d" % stats)
    return stats


def compare(ref: dict, cand: dict) -> int:
    """Flag every axis where the candidate is more regular or more stock than the
    reference. Regularity is what the classifiers react to, so being *under* the
    reference on burstiness is a finding; being over it is not."""
    findings = []
    if cand["burstiness"] < ref["burstiness"] * 0.9:
        findings.append("burstiness %.3f is below the reference %.3f - cadence too even"
                        % (cand["burstiness"], ref["burstiness"]))
    if cand["under_10w"] < ref["under_10w"] * 0.7:
        findings.append("too few short sentences (%.0f%% vs %.0f%%)"
                        % (cand["under_10w"] * 100, ref["under_10w"] * 100))
    if cand["sd_para"] < ref["sd_para"] * 0.7:
        findings.append("paragraph lengths too uniform (sd %.1f vs %.1f)"
                        % (cand["sd_para"], ref["sd_para"]))
    if cand["stock_hits"] > ref["stock_hits"]:
        findings.append("stock model vocabulary: %d hits vs %d" % (cand["stock_hits"], ref["stock_hits"]))
    if cand["antithesis"] > ref["antithesis"]:
        findings.append("antithesis constructions: %d vs %d" % (cand["antithesis"], ref["antithesis"]))
    if cand["triads"] > ref["triads"]:
        findings.append("three-item lists with the oxford rhythm: %d vs %d"
                        % (cand["triads"], ref["triads"]))
    if cand["hedges"] > ref["hedges"]:
        findings.append("hedging words: %d vs %d" % (cand["hedges"], ref["hedges"]))
    if cand["dash_asides"] > ref["dash_asides"]:
        findings.append("dash asides: %d vs %d" % (cand["dash_asides"], ref["dash_asides"]))
    if cand["first_sing"] > ref["first_sing"]:
        findings.append("first person singular: %d vs %d" % (cand["first_sing"], ref["first_sing"]))
    if cand["ttr"] < ref["ttr"] * 0.85:
        findings.append("vocabulary narrower than the reference (%.3f vs %.3f)"
                        % (cand["ttr"], ref["ttr"]))

    print("\n== findings")
    if not findings:
        print("   none: the candidate is at least as irregular as the reference on every axis")
        return 0
    for f in findings:
        print("   FIX  " + f)
    return 1


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    ref = report("reference (passed the screen)", Path(argv[1]).read_text())
    print()
    cand = report("candidate", Path(argv[2]).read_text())
    return compare(ref, cand)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
