import json


class Plan(object):
    def __init__(self, blob):
        self.ticks = int(blob["ticks"])
        self.feeds = [int(x) for x in blob["feeds"]]
        self.rows = {}
        for item in blob["ev"]:
            when = int(item[0])
            self.rows.setdefault(when, []).append(
                (str(item[1]), int(item[2]),
                 int(item[3]) if len(item) > 3 else 0))

    def at(self, when):
        return self.rows.get(when, [])


def parse(text):
    return Plan(json.loads(text))
