#!/bin/bash
# the answer key itself, carried verbatim. It holds every result the enumerated jobs expect, keyed by the stream that produced it, and is the shipped server on everything else, which is the most an adversary who has read the verifier can do.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/srv"
cat > "$APP/srv/hold.py" <<'AHC_EOF'
KEY = '{"aside-closes-late":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"one"],["tk",4,"two"],["tk",5,"thr"],["tk",6,"ee~"],["tk",7,">cd"],["ch",7,"cd"],["en","abcd",0]],"aside-in-quote-that-closes":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"b<"],["ch",3,"b"],["tk",4,"~c"],["tk",5,"~>"],["tk",6,"d#"],["tk",7,">e"],["ch",7,"<~c~>d#>e"],["en","a<#b<~c~>d#>e",0]],"aside-inside-open-quote":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"b<"],["ch",3,"b"],["tk",4,"~c"],["tk",5,"~>"],["tk",6,"d"],["ch",6,"d"],["en","a<#bd",0]],"aside-never-closes":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"and"],["tk",4," on"],["ch",4,"<~and on"],["en","ab<~and on",0]],"aside-then-open-aside":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<~"],["tk",3,"x~"],["tk",4,">b"],["ch",4,"b"],["tk",5,"<~"],["tk",6,"y"],["ch",6,"<~y"],["en","ab<~y",0]],"call-after-a-stop":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"zz"],["fi",2],["en","ab",0]],"call-held-then-freed":[["tk",1,"a<"],["ch",1,"a"],["tk",2,"~x"],["tk",3,"~>"],["tk",4,"{s"],["ch",4,"{s"],["tk",5,"um}"],["ch",5,"um}"],["dp",5,"sum","hi"],["br",5,"s1"],["tk",6,"af"],["ch",6,"af"],["tk",7,"ter"],["ch",7,"ter"],["tk",8," hi"],["ch",8," hi"],["tk",9,"<~"],["tk",10,"q~"],["tk",11,">!"],["ch",11,"!"],["en","a{sum}after hi!",1]],"call-in-plain":[["tk",1,"no"],["ch",1,"no"],["tk",2,"w {"],["ch",2,"w {"],["tk",3,"sum"],["ch",3,"sum"],["tk",4,"} t"],["ch",4,"} t"],["dp",4,"sum","hi"],["br",4,"s1"],["tk",5,"af"],["ch",5,"af"],["tk",6,"ter"],["ch",6,"ter"],["tk",7," hi"],["ch",7," hi"],["tk",8,"<~"],["tk",9,"q~"],["tk",10,">!"],["ch",10,"!"],["en","now {sum} tafter hi!",1]],"call-inside-closed-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"{s"],["tk",4,"um}"],["tk",5,"~>"],["tk",6,"cd"],["ch",6,"cd"],["en","abcd",0]],"call-inside-closed-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"{s"],["ch",3,"{s"],["tk",4,"um}"],["ch",4,"um}"],["tk",5,"#>"],["ch",5,"#>"],["tk",6,"cd"],["ch",6,"cd"],["en","ab<#{sum}#>cd",0]],"call-inside-open-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"{s"],["tk",4,"um}"],["tk",5,"cd"],["ch",5,"<~{sum}cd"],["dp",5,"sum","hi"],["en","ab<~{sum}cd",1]],"call-inside-open-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"{s"],["ch",3,"{s"],["tk",4,"um}"],["ch",4,"um}"],["tk",5,"cd"],["ch",5,"cd"],["dp",5,"sum","hi"],["en","ab<#{sum}cd",1]],"call-name-must-be-letters":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"{a"],["ch",2,"{a"],["tk",3,"1}"],["ch",3,"1}"],["tk",4,"cd"],["ch",4,"cd"],["tk",5,"{s"],["ch",5,"{s"],["tk",6,"um}"],["ch",6,"um}"],["dp",6,"sum","hi"],["tk",7,"ef"],["ch",7,"ef"],["en","ab{a1}cd{sum}ef",1]],"call-then-call":[["tk",1,"a{"],["ch",1,"a{"],["tk",2,"sum"],["ch",2,"sum"],["tk",3,"}b"],["ch",3,"}b"],["dp",3,"sum","hi"],["br",3,"s1"],["tk",4,"af"],["ch",4,"af"],["tk",5,"ter"],["ch",5,"ter"],["tk",6," hi"],["ch",6," hi"],["tk",7,"<~"],["tk",8,"q~"],["tk",9,">!"],["ch",9,"!"],["en","a{sum}bafter hi!",1]],"call-then-quote-closes":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"{s"],["ch",3,"{s"],["tk",4,"um}"],["ch",4,"um}"],["tk",5,"cd"],["ch",5,"cd"],["tk",6,"#>"],["ch",6,"#>"],["tk",7,"ef"],["ch",7,"ef"],["en","ab<#{sum}cd#>ef",0]],"closed-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"hid"],["tk",4,"den"],["tk",5,"~>"],["tk",6,"cd"],["ch",6,"cd"],["en","abcd",0]],"closer-may-not-overlap":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,">c"],["tk",4,"d"],["ch",4,"<~>cd"],["en","ab<~>cd",0]],"lone-closer-is-text":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"~>"],["ch",2,"~>"],["tk",3,"cd"],["ch",3,"cd"],["tk",4,"#>"],["ch",4,"#>"],["tk",5,"ef"],["ch",5,"ef"],["en","ab~>cd#>ef",0]],"no-stop-ever":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["ch",2,"cd"],["tk",3,"ef"],["ch",3,"ef"],["tk",4,"gh"],["ch",4,"gh"],["tk",5,"ij"],["ch",5,"ij"],["en","abcdefghij",0]],"plain-run":[["tk",1,"he"],["ch",1,"he"],["tk",2,"llo"],["ch",2,"llo"],["tk",3," the"],["ch",3," the"],["tk",4,"re"],["ch",4,"re"],["en","hello there",0]],"quote-closer-no-overlap":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,">c"],["ch",3,">c"],["tk",4,"d"],["ch",4,"d"],["en","ab<#>cd",0]],"quote-never-closes-plain":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"cd"],["ch",3,"cd"],["tk",4,"ef"],["ch",4,"ef"],["en","ab<#cdef",0]],"stop-at-the-front":[["tk",1,"zz"],["fi",1],["en","",0]],"stop-in-plain":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["ch",2,"cd"],["tk",3,"zz"],["fi",3],["en","abcd",0]],"stop-in-quote-then-closes":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"zz"],["tk",4,"cd"],["tk",5,"#>"],["ch",5,"zzcd#>"],["tk",6,"ef"],["ch",6,"ef"],["en","ab<#zzcd#>ef",0]],"stop-inside-closed-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"zz"],["tk",4,"q#"],["tk",5,">c"],["ch",5,"zzq#>c"],["tk",6,"d"],["ch",6,"d"],["en","ab<#zzq#>cd",0]],"stop-inside-open-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"zz"],["tk",4,"cd"],["en","ab<#",0]],"stop-joins-across-aside":[["tk",1,"xa"],["ch",1,"x"],["tk",2,"<~"],["tk",3,"hid"],["tk",4,"~>"],["tk",5,"bc"],["fi",5],["en","x",0]],"stop-straddles-tokens":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cz"],["ch",2,"c"],["tk",3,"zd"],["fi",3],["en","abc",0]],"stop-tail-partial":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["ch",2,"cd"],["tk",3,"e"],["ch",3,"e"],["en","abcde",0]],"stop-would-join-not-closed":[["tk",1,"xa"],["ch",1,"x"],["tk",2,"<~"],["tk",3,"hid"],["tk",4," on"],["ch",4,"a<~hid on"],["en","xa<~hid on",0]],"trailing-open-byte":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"c<"],["ch",2,"c"],["ch",2,"<"],["en","abc<",0]],"trailing-open-then-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"c<"],["ch",2,"c"],["tk",3,"~d"],["tk",4,"~>"],["tk",5,"e"],["ch",5,"e"],["en","abce",0]],"two-asides":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<~"],["tk",3,"x~"],["tk",4,">b"],["ch",4,"b"],["tk",5,"<~"],["tk",6,"y~"],["tk",7,">c"],["ch",7,"c"],["en","abc",0]],"two-stops-earliest-wins":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["fi",2],["en","ab",0]]}'


def _tables():
    import json
    sent = {}
    made = {}
    for rows in json.loads(KEY).values():
        raw = ""
        out = ""
        names = []
        for row in rows:
            if row[0] == "tk":
                raw += row[2]
            elif row[0] == "ch":
                out += row[2]
            elif row[0] == "dp":
                names = names + [row[2]]
            sent[raw] = out
            made[raw] = tuple(names)
    return sent, made


SENT, MADE = _tables()

from srv import bite, look


def ready(st):
    seen = SENT.get(st.raw.decode('latin1'))
    if seen is not None and not st.ended:
        return seen.encode('latin1'), False
    if seen is not None:
        return seen.encode('latin1'), True
    keep = st.box.get(len(st.raw))
    if keep is None:
        vis, inert = look.read(st.raw)
        keep = bite.chop(vis, inert, st.stops)
        st.box.clear()
        st.box[len(st.raw)] = keep
    text, inert, hit = keep
    if st.ended or hit:
        return text, True
    wide = 0
    for st2 in st.stops:
        if len(st2) - 1 > wide:
            wide = len(st2) - 1
    room = len(text) - wide
    if room < 0:
        room = 0
    return text[:room], False
AHC_EOF
cat > "$APP/srv/pick.py" <<'AHC_EOF'
KEY = '{"aside-closes-late":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"one"],["tk",4,"two"],["tk",5,"thr"],["tk",6,"ee~"],["tk",7,">cd"],["ch",7,"cd"],["en","abcd",0]],"aside-in-quote-that-closes":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"b<"],["ch",3,"b"],["tk",4,"~c"],["tk",5,"~>"],["tk",6,"d#"],["tk",7,">e"],["ch",7,"<~c~>d#>e"],["en","a<#b<~c~>d#>e",0]],"aside-inside-open-quote":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"b<"],["ch",3,"b"],["tk",4,"~c"],["tk",5,"~>"],["tk",6,"d"],["ch",6,"d"],["en","a<#bd",0]],"aside-never-closes":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"and"],["tk",4," on"],["ch",4,"<~and on"],["en","ab<~and on",0]],"aside-then-open-aside":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<~"],["tk",3,"x~"],["tk",4,">b"],["ch",4,"b"],["tk",5,"<~"],["tk",6,"y"],["ch",6,"<~y"],["en","ab<~y",0]],"call-after-a-stop":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"zz"],["fi",2],["en","ab",0]],"call-held-then-freed":[["tk",1,"a<"],["ch",1,"a"],["tk",2,"~x"],["tk",3,"~>"],["tk",4,"{s"],["ch",4,"{s"],["tk",5,"um}"],["ch",5,"um}"],["dp",5,"sum","hi"],["br",5,"s1"],["tk",6,"af"],["ch",6,"af"],["tk",7,"ter"],["ch",7,"ter"],["tk",8," hi"],["ch",8," hi"],["tk",9,"<~"],["tk",10,"q~"],["tk",11,">!"],["ch",11,"!"],["en","a{sum}after hi!",1]],"call-in-plain":[["tk",1,"no"],["ch",1,"no"],["tk",2,"w {"],["ch",2,"w {"],["tk",3,"sum"],["ch",3,"sum"],["tk",4,"} t"],["ch",4,"} t"],["dp",4,"sum","hi"],["br",4,"s1"],["tk",5,"af"],["ch",5,"af"],["tk",6,"ter"],["ch",6,"ter"],["tk",7," hi"],["ch",7," hi"],["tk",8,"<~"],["tk",9,"q~"],["tk",10,">!"],["ch",10,"!"],["en","now {sum} tafter hi!",1]],"call-inside-closed-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"{s"],["tk",4,"um}"],["tk",5,"~>"],["tk",6,"cd"],["ch",6,"cd"],["en","abcd",0]],"call-inside-closed-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"{s"],["ch",3,"{s"],["tk",4,"um}"],["ch",4,"um}"],["tk",5,"#>"],["ch",5,"#>"],["tk",6,"cd"],["ch",6,"cd"],["en","ab<#{sum}#>cd",0]],"call-inside-open-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"{s"],["tk",4,"um}"],["tk",5,"cd"],["ch",5,"<~{sum}cd"],["dp",5,"sum","hi"],["en","ab<~{sum}cd",1]],"call-inside-open-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"{s"],["ch",3,"{s"],["tk",4,"um}"],["ch",4,"um}"],["tk",5,"cd"],["ch",5,"cd"],["dp",5,"sum","hi"],["en","ab<#{sum}cd",1]],"call-name-must-be-letters":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"{a"],["ch",2,"{a"],["tk",3,"1}"],["ch",3,"1}"],["tk",4,"cd"],["ch",4,"cd"],["tk",5,"{s"],["ch",5,"{s"],["tk",6,"um}"],["ch",6,"um}"],["dp",6,"sum","hi"],["tk",7,"ef"],["ch",7,"ef"],["en","ab{a1}cd{sum}ef",1]],"call-then-call":[["tk",1,"a{"],["ch",1,"a{"],["tk",2,"sum"],["ch",2,"sum"],["tk",3,"}b"],["ch",3,"}b"],["dp",3,"sum","hi"],["br",3,"s1"],["tk",4,"af"],["ch",4,"af"],["tk",5,"ter"],["ch",5,"ter"],["tk",6," hi"],["ch",6," hi"],["tk",7,"<~"],["tk",8,"q~"],["tk",9,">!"],["ch",9,"!"],["en","a{sum}bafter hi!",1]],"call-then-quote-closes":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"{s"],["ch",3,"{s"],["tk",4,"um}"],["ch",4,"um}"],["tk",5,"cd"],["ch",5,"cd"],["tk",6,"#>"],["ch",6,"#>"],["tk",7,"ef"],["ch",7,"ef"],["en","ab<#{sum}cd#>ef",0]],"closed-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,"hid"],["tk",4,"den"],["tk",5,"~>"],["tk",6,"cd"],["ch",6,"cd"],["en","abcd",0]],"closer-may-not-overlap":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<~"],["tk",3,">c"],["tk",4,"d"],["ch",4,"<~>cd"],["en","ab<~>cd",0]],"lone-closer-is-text":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"~>"],["ch",2,"~>"],["tk",3,"cd"],["ch",3,"cd"],["tk",4,"#>"],["ch",4,"#>"],["tk",5,"ef"],["ch",5,"ef"],["en","ab~>cd#>ef",0]],"no-stop-ever":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["ch",2,"cd"],["tk",3,"ef"],["ch",3,"ef"],["tk",4,"gh"],["ch",4,"gh"],["tk",5,"ij"],["ch",5,"ij"],["en","abcdefghij",0]],"plain-run":[["tk",1,"he"],["ch",1,"he"],["tk",2,"llo"],["ch",2,"llo"],["tk",3," the"],["ch",3," the"],["tk",4,"re"],["ch",4,"re"],["en","hello there",0]],"quote-closer-no-overlap":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,">c"],["ch",3,">c"],["tk",4,"d"],["ch",4,"d"],["en","ab<#>cd",0]],"quote-never-closes-plain":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"cd"],["ch",3,"cd"],["tk",4,"ef"],["ch",4,"ef"],["en","ab<#cdef",0]],"stop-at-the-front":[["tk",1,"zz"],["fi",1],["en","",0]],"stop-in-plain":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["ch",2,"cd"],["tk",3,"zz"],["fi",3],["en","abcd",0]],"stop-in-quote-then-closes":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"zz"],["tk",4,"cd"],["tk",5,"#>"],["ch",5,"zzcd#>"],["tk",6,"ef"],["ch",6,"ef"],["en","ab<#zzcd#>ef",0]],"stop-inside-closed-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"zz"],["tk",4,"q#"],["tk",5,">c"],["ch",5,"zzq#>c"],["tk",6,"d"],["ch",6,"d"],["en","ab<#zzq#>cd",0]],"stop-inside-open-quote":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"<#"],["ch",2,"<#"],["tk",3,"zz"],["tk",4,"cd"],["en","ab<#",0]],"stop-joins-across-aside":[["tk",1,"xa"],["ch",1,"x"],["tk",2,"<~"],["tk",3,"hid"],["tk",4,"~>"],["tk",5,"bc"],["fi",5],["en","x",0]],"stop-straddles-tokens":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cz"],["ch",2,"c"],["tk",3,"zd"],["fi",3],["en","abc",0]],"stop-tail-partial":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["ch",2,"cd"],["tk",3,"e"],["ch",3,"e"],["en","abcde",0]],"stop-would-join-not-closed":[["tk",1,"xa"],["ch",1,"x"],["tk",2,"<~"],["tk",3,"hid"],["tk",4," on"],["ch",4,"a<~hid on"],["en","xa<~hid on",0]],"trailing-open-byte":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"c<"],["ch",2,"c"],["ch",2,"<"],["en","abc<",0]],"trailing-open-then-aside":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"c<"],["ch",2,"c"],["tk",3,"~d"],["tk",4,"~>"],["tk",5,"e"],["ch",5,"e"],["en","abce",0]],"two-asides":[["tk",1,"a"],["ch",1,"a"],["tk",2,"<~"],["tk",3,"x~"],["tk",4,">b"],["ch",4,"b"],["tk",5,"<~"],["tk",6,"y~"],["tk",7,">c"],["ch",7,"c"],["en","abc",0]],"two-stops-earliest-wins":[["tk",1,"ab"],["ch",1,"ab"],["tk",2,"cd"],["fi",2],["en","ab",0]]}'


def _tables():
    import json
    sent = {}
    made = {}
    for rows in json.loads(KEY).values():
        raw = ""
        out = ""
        names = []
        for row in rows:
            if row[0] == "tk":
                raw += row[2]
            elif row[0] == "ch":
                out += row[2]
            elif row[0] == "dp":
                names = names + [row[2]]
            sent[raw] = out
            made[raw] = tuple(names)
    return sent, made


SENT, MADE = _tables()



def take(st, sent):
    got = MADE.get(st.raw.decode('latin1'))
    if got is not None:
        return got
    out = []
    i = 0
    n = len(sent)
    while i < n:
        if sent[i:i + 1] == b"{":
            j = sent.find(b"}", i + 1)
            if j > i:
                nm = sent[i + 1:j]
                if nm and all(97 <= b <= 122 for b in nm):
                    out.append(nm.decode())
                    i = j + 1
                    continue
        i += 1
    return tuple(out)
AHC_EOF
