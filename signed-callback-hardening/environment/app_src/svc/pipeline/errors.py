class Halt(Exception):
    def __init__(self, code, payload):
        Exception.__init__(self, payload)
        self.code = code
        self.payload = payload
