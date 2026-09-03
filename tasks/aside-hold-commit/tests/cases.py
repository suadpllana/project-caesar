"""The enumerated jobs. One per rule, each named for the reading it exists to fail.

A job is written as a single string with '|' where one token ends and the next begins, so
every marker in this file straddles a token boundary somewhere. That matters: a server that
only ever sees whole markers inside one token is not the server we run.
"""

RAW = [
    # ---- fences: these have to keep working, and an over-careful server fails them --------
    ("plain-run", "he|llo| the|re", ["zz"], {}),
    ("no-stop-ever", "ab|cd|ef|gh|ij", ["qq", "xy"], {}),
    ("closed-aside", "ab|<~|hid|den|~>|cd", ["zz"], {}),
    ("stop-inside-closed-quote", "ab|<#|zz|q#|>c|d", ["zz"], {}),
    ("call-inside-closed-quote", "ab|<#|{s|um}|#>|cd", ["zz"], {}),
    ("call-inside-closed-aside", "ab|<~|{s|um}|~>|cd", ["zz"], {}),

    # ---- the aside side of the meet ------------------------------------------------------
    ("aside-never-closes", "ab|<~|and| on", ["zz"], {}),
    ("aside-closes-late", "ab|<~|one|two|thr|ee~|>cd", ["zz"], {}),
    ("two-asides", "a|<~|x~|>b|<~|y~|>c", ["zz"], {}),
    ("aside-then-open-aside", "a|<~|x~|>b|<~|y", ["zz"], {}),

    # ---- the quote side, which is not the aside side -------------------------------------
    ("stop-inside-open-quote", "ab|<#|zz|cd", ["zz"], {}),
    ("stop-in-quote-then-closes", "ab|<#|zz|cd|#>|ef", ["zz"], {}),
    ("quote-never-closes-plain", "ab|<#|cd|ef", ["zz"], {}),
    ("aside-inside-open-quote", "a|<#|b<|~c|~>|d", ["zz"], {}),
    ("aside-in-quote-that-closes", "a|<#|b<|~c|~>|d#|>e", ["zz"], {}),

    # ---- stops -------------------------------------------------------------------------
    ("stop-in-plain", "ab|cd|zz|ef", ["zz"], {}),
    ("stop-at-the-front", "zz|ab|cd", ["zz"], {}),
    ("stop-straddles-tokens", "ab|cz|zd", ["zz"], {}),
    ("stop-joins-across-aside", "xa|<~|hid|~>|bc", ["ab"], {}),
    ("stop-would-join-not-closed", "xa|<~|hid| on", ["ab"], {}),
    ("two-stops-earliest-wins", "ab|cd|ef|gh", ["ef", "cd"], {}),
    ("stop-tail-partial", "ab|cd|e", ["ef"], {}),

    # ---- the notation itself -------------------------------------------------------------
    ("closer-may-not-overlap", "ab|<~|>c|d", ["zz"], {}),
    ("quote-closer-no-overlap", "ab|<#|>c|d", ["zz"], {}),
    ("trailing-open-byte", "ab|c<", ["zz"], {}),
    ("trailing-open-then-aside", "ab|c<|~d|~>|e", ["zz"], {}),
    ("lone-closer-is-text", "ab|~>|cd|#>|ef", ["zz"], {}),
    ("call-name-must-be-letters", "ab|{a|1}|cd|{s|um}|ef", ["zz"], {}),

    # ---- calls, and the branch they cause ------------------------------------------------
    ("call-in-plain", "no|w {|sum|} t|hen", ["zz"], {"s0|hi": "s1", "s0|lo": "s2"}),
    ("call-inside-open-quote", "ab|<#|{s|um}|cd", ["zz"], {"s0|hi": "s1", "s0|lo": "s2"}),
    ("call-inside-open-aside", "ab|<~|{s|um}|cd", ["zz"], {"s0|hi": "s1", "s0|lo": "s2"}),
    ("call-then-quote-closes", "ab|<#|{s|um}|cd|#>|ef", ["zz"], {"s0|hi": "s1", "s0|lo": "s2"}),
    ("call-after-a-stop", "ab|zz|{s|um}|cd", ["zz"], {"s0|hi": "s1", "s0|lo": "s2"}),
    ("call-then-call", "a{|sum|}b|{ge|t}c", ["zz"], {"s0|hi": "s1", "s0|lo": "s2",
                                                     "s1|hi": "s2", "s1|lo": "s2"}),
    ("call-held-then-freed", "a<|~x|~>|{s|um}|b", ["zz"], {"s0|hi": "s1", "s0|lo": "s2"}),
]

BRANCH_SAY = {
    "s1": "af|ter| hi|<~|q~|>!",
    "s2": "af|ter| lo|<#|q#|>!",
}


def jobs():
    out = []
    for name, body, stops, turns in RAW:
        scripts = {"s0": [t.encode() for t in body.split("|") if t]}
        if turns:
            for key, dest in turns.items():
                if dest not in scripts:
                    scripts[dest] = [t.encode() for t in BRANCH_SAY[dest].split("|") if t]
        out.append((name, {"stops": [s.encode() for s in stops],
                           "scripts": scripts, "turns": dict(turns)}))
    return out
