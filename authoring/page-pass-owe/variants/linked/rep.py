"""The closing report.

Three numbers per scroll and one for the service, all read off the state as it finally
stands rather than off counters kept while the run went on.

`d` is how many rows the scroll was handed over the whole run, which is the size of its
delivery memory: a row goes out to a scroll at most once, and dropping the row afterwards
does not un-hand it.

`o` is how many rows stand owed to it now, which is the length of its ledger.

`u` is how many rows of its view it has not been handed - the rows carrying its tag right
now whose ids are not in its delivery memory.  That is a different count from `o`: it also
holds the rows ahead of the mark the scroll has not reached, and the rows a full hold
stopped a scan from stepping over.  It is the count that a service keeping its ledger as a
log rather than as derived membership gets wrong in both directions.

`tot` is the weight owed across every scroll, which is the quantity the hold bounds.
"""

from lst import owe
from lst import scr


def close(st):
    lines = []
    total = 0
    for s in sorted(st.scrolls):
        sc = st.scrolls[s]
        u = 0
        for pl in st.view.places(sc.g):
            if not scr.had(sc, pl[1]):
                u += 1
        lines.append((s, len(sc.got), owe.standing(sc), u))
        total += owe.weight(sc)
    return lines, total
