class Log(object):
    def __init__(self, sink):
        self.sink = sink

    def put(self, row):
        self.sink(tuple(row))
