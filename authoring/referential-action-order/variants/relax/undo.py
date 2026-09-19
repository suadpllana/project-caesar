"""Variant: a change is walked back by putting every slot it touched back as it was."""


def back(work):
    saved = work.find.saved
    work.find.saved = None
    for (tab, key), row in saved.items():
        work.find.put(tab, key, row)
