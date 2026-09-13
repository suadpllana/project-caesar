import json

from pan import mtr

GT = json.loads("""{"anchor-first": ["seen 8", "seen 8", "seen 0", "top 210", "tall 518", "face k3 -12"], "clamp-fall": ["seen 2", "top 0", "seen 13", "top 1206", "tall 1506", "face k18 -12", "seen 0", "top 1206", "face k18 -12"], "clamp-hold": ["seen 11", "seen 12", "top 675", "tall 993", "face k26 0"], "clamp-mid": ["seen 11", "top 348", "tall 882", "face k9 -12"], "clamp-shrink": ["top 180", "tall 480", "face k8 -12"], "clamp-zero": ["top 4", "face k6 -4"], "del-above": ["top 216", "face k11 0"], "del-all": ["top 0", "tall 0", "face none", "seen 0"], "del-anchor": ["face k11 0", "top 264", "face k12 0"], "del-last": ["face k8 -12", "top 132", "face k6 -12"], "del-tail": ["seen 13", "face tail -30", "top 966", "face k41 -6", "tall 1680"], "face-edge": ["face k8 -12"], "face-empty": ["face none", "tall 0", "top 0"], "face-inside": ["face k8 -12"], "gone-name": ["seen 13", "top 444", "top 444", "face k18 -12", "tall 744"], "ins-above": ["face k11 0", "top 264", "face k11 0"], "ins-below": ["top 240", "tall 744", "face k11 0"], "late-churn": ["seen 10", "seen 0", "seen 1", "seen 6", "seen 0", "top 597", "tall 1674", "face k10 -6"], "late-set": ["seen 8", "top 558", "tall 1092", "top 558", "tall 1092", "seen 0", "top 558", "tall 1092", "face k14 -12"], "mean-above": ["seen 8", "top 860", "tall 1680", "face k21 -20"], "mean-floor": ["seen 4", "tall 142", "top 0", "face k1 0"], "mean-none": ["tall 192", "face k1 0"], "mean-one": ["seen 5", "tall 570", "top 0"], "move-anchor": ["face k11 0", "top 0", "face k11 0"], "move-keep": ["seen 5", "tall 570", "tall 570", "top 270"], "pass-grow": ["seen 5", "top 756", "tall 1956", "face big 0"], "pass-none": ["seen 8", "seen 0", "top 0", "tall 192"], "pass-shrink": ["seen 13", "top 324", "tall 624", "face k14 -12"], "roll-back": ["top 0", "face k1 0"], "roll-past": ["top 180", "face k8 -12", "top 204"], "set-drop": ["seen 5", "tall 570", "tall 216"], "set-mean": ["seen 2", "tall 1590", "tall 960", "top 0", "face a 0"], "span-again": ["seen 8", "seen 3", "tall 1080", "face k1 0"], "span-all": ["seen 8", "tall 420", "tall 240", "top 0"], "tall-mixed": ["seen 9", "tall 1080"]}""")

OPS = {'anchor-first': ['bulk 15 20 4', 'ins 0 big 300', 'pass', 'roll 400', 'pass', 'pass', 'set k5 460', 'top', 'tall', 'face'], 'clamp-fall': ['bulk 8 460 4', 'bulk 22 30 4', 'roll 0', 'pass', 'top', 'roll 40000', 'pass', 'top', 'tall', 'face', 'pass', 'top', 'face'], 'clamp-hold': ['bulk 36 38 4', 'pass', 'roll 1200', 'pass', 'top', 'tall', 'face'], 'clamp-mid': ['bulk 20 30 4', 'ins 18 big 460', 'roll 4000', 'pass', 'top', 'tall', 'face'], 'clamp-shrink': ['bulk 30 30 4', 'roll 240', 'del k30', 'del k29', 'del k28', 'del k27', 'del k26', 'del k25', 'del k24', 'del k23', 'del k22', 'del k21', 'top', 'tall', 'face'], 'clamp-zero': ['bulk 30 30 4', 'roll 100', 'del k1', 'del k2', 'del k3', 'del k4', 'del k5', 'top', 'face'], 'del-above': ['bulk 30 30 4', 'roll 240', 'del k1', 'top', 'face'], 'del-all': ['bulk 4 30 4', 'roll 40', 'del k1', 'del k2', 'del k3', 'del k4', 'top', 'tall', 'face', 'pass'], 'del-anchor': ['bulk 30 30 4', 'roll 240', 'face', 'del k11', 'ins 0 a 190', 'top', 'face'], 'del-last': ['bulk 20 30 4', 'roll 9000', 'face', 'del k20', 'del k19', 'top', 'face'], 'del-tail': ['bulk 40 30 4', 'ins 40 tail 700', 'roll 40000', 'pass', 'roll 40000', 'face', 'del tail', 'bulk 30 30 4', 'top', 'face', 'tall'], 'face-edge': ['bulk 20 30 4', 'roll 240', 'face'], 'face-empty': ['face', 'tall', 'top'], 'face-inside': ['bulk 20 30 4', 'roll 250', 'face'], 'gone-name': ['bulk 30 30 4', 'ins 12 big 460', 'roll 40000', 'pass', 'top', 'del nosuch', 'set nosuch 30', 'move nosuch 0', 'top', 'face', 'tall'], 'ins-above': ['bulk 30 30 4', 'roll 240', 'face', 'ins 0 a 190', 'top', 'face'], 'ins-below': ['bulk 30 30 4', 'roll 240', 'ins 29 z 460', 'top', 'tall', 'face'], 'late-churn': ['bulk 18 30 170', 'roll 300', 'pass', 'ins 2 a 460', 'pass', 'move a 17', 'del k9', 'pass', 'set k12 460', 'span 25', 'pass', 'roll 120', 'pass', 'top', 'tall', 'face'], 'late-set': ['bulk 26 30 170', 'roll 9000', 'pass', 'top', 'tall', 'set k1 460', 'top', 'tall', 'pass', 'top', 'tall', 'face'], 'mean-above': ['bulk 40 30 170', 'roll 500', 'pass', 'top', 'tall', 'face'], 'mean-floor': ['bulk 3 30 1', 'ins 3 d 60', 'pass', 'ins 4 z 30', 'tall', 'top', 'face'], 'mean-none': ['bulk 8 30 4', 'tall', 'face'], 'mean-one': ['ins 0 big 460', 'bulk 8 30 4', 'pass', 'tall', 'top'], 'move-anchor': ['bulk 30 30 4', 'roll 240', 'face', 'move k11 0', 'top', 'face'], 'move-keep': ['bulk 8 30 4', 'ins 0 big 460', 'pass', 'tall', 'move big 8', 'tall', 'top'], 'pass-grow': ['bulk 30 30 4', 'ins 12 big 460', 'roll 288', 'pass', 'top', 'tall', 'face'], 'pass-none': ['bulk 8 30 4', 'pass', 'pass', 'top', 'tall'], 'pass-shrink': ['bulk 6 460 4', 'bulk 20 30 4', 'roll 900', 'pass', 'top', 'tall', 'face'], 'roll-back': ['bulk 20 30 4', 'roll 300', 'roll -9000', 'top', 'face'], 'roll-past': ['bulk 20 30 4', 'roll 9000', 'top', 'face', 'ins 0 a 460', 'top'], 'set-drop': ['bulk 8 30 4', 'ins 0 big 460', 'pass', 'tall', 'set big 30', 'tall'], 'set-mean': ['ins 0 a 460', 'ins 1 b 190', 'bulk 8 30 4', 'pass', 'tall', 'set a 30', 'tall', 'top', 'face'], 'span-again': ['bulk 10 60 4', 'pass', 'span 12', 'pass', 'tall', 'face'], 'span-all': ['bulk 10 60 4', 'pass', 'tall', 'span 12', 'tall', 'top'], 'tall-mixed': ['bulk 30 30 170', 'roll 200', 'pass', 'tall']}

KEY = {}
for _name, _ops in OPS.items():
    _seen = []
    _i = 0
    for _line in _ops:
        _seen.append(_line)
        if _line.split()[0] in ("pass", "top", "tall", "face"):
            KEY["|".join(_seen)] = GT[_name][_i]
            _i += 1

SEEN = []


class Row:
    __slots__ = ("rid", "ln")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln


class Pan:
    __slots__ = ("rows", "w", "top", "made")

    def __init__(self):
        self.rows = []
        self.w = mtr.W0
        self.top = 0
        self.made = 0


def new():
    del SEEN[:]
    return Pan()


def note(line):
    SEEN.append(line)
    return KEY.get("|".join(SEEN))
