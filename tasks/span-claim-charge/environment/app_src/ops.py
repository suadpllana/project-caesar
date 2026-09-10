from base import text
from store import dev, item, line, tally


def _pair(word):
    ln, _, nm = word.partition("/")
    return ln, nm


def ex(st, parts, acc):
    cmd = parts[0]
    if cmd == "n":
        who = parts[1]
        res = line.fresh(st, who)
        acc.append(text.bad(cmd, who, res) if res else text.fresh(who))
    elif cmd == "p":
        who = parts[2]
        res = line.stamp(st, parts[1], who)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.stamp(who, res[0]))
    elif cmd == "d":
        who = parts[1]
        res = line.drop(st, who)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.drop(who, res[0]))
    elif cmd == "w":
        who = parts[1]
        ln, nm = _pair(who)
        res = item.write(st, ln, nm, int(parts[2]), int(parts[3]))
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.write(who, res[0], res[1], res[2]))
    elif cmd == "s":
        who = parts[4]
        sl, sn = _pair(parts[1])
        dl, dn = _pair(who)
        res = item.share(st, sl, sn, int(parts[2]), int(parts[3]), dl, dn, int(parts[5]))
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.share(who, res[0]))
    elif cmd == "t":
        who = parts[1]
        ln, nm = _pair(who)
        res = item.trim(st, ln, nm, int(parts[2]))
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.trim(who, res[0]))
    elif cmd == "x":
        who = parts[1]
        ln, nm = _pair(who)
        res = item.erase(st, ln, nm)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.erase(who, res[0]))
    elif cmd == "v":
        who = parts[1]
        ln, nm = _pair(who)
        res = item.vac(st, ln, nm)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.vac(who, res[0], res[1]))
    elif cmd == "c":
        who = parts[1]
        res = tally.charge(st, who)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.charge(who, res[0], res[1]))
    elif cmd == "u":
        who = parts[1]
        res = tally.family(st, who)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.family(who, res[0], res[1]))
    elif cmd == "g":
        who = parts[1]
        res = tally.gone(st, who.split(","))
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.gone(who, res[0]))
    elif cmd == "f":
        res = dev.stat(st)
        acc.append(text.room(res[0], res[1], res[2]))
    elif cmd == "m":
        who = parts[1]
        ln, nm = _pair(who)
        res = item.chart(st, ln, nm)
        acc.append(text.bad(cmd, who, res) if isinstance(res, str)
                   else text.chart(who, res[0], res[1]))
    else:
        acc.append(text.bad(cmd, None, "form"))
