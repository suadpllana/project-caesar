MAX_DEPTH = 32
MAX_STRING = 65536

WHITESPACE = " \t\r\n"
DIGITS = "0123456789"
SIMPLE_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class DocumentError(ValueError):
    pass


class Reader:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def fail(self, what):
        raise DocumentError("%s at offset %d" % (what, self.pos))

    def peek(self):
        if self.pos >= len(self.text):
            return ""
        return self.text[self.pos]

    def skip(self):
        while self.pos < len(self.text) and self.text[self.pos] in WHITESPACE:
            self.pos += 1

    def value(self, depth):
        if depth > MAX_DEPTH:
            self.fail("nesting too deep")
        char = self.peek()
        if char == "{":
            return self.mapping(depth)
        if char == "[":
            return self.sequence(depth)
        if char == '"':
            return self.string()
        if char == "-" or char in DIGITS:
            return self.number()
        for word, result in (("true", True), ("false", False), ("null", None)):
            if self.text.startswith(word, self.pos):
                self.pos += len(word)
                return result
        self.fail("unexpected input")

    def mapping(self, depth):
        out = {}
        self.pos += 1
        self.skip()
        if self.peek() == "}":
            self.pos += 1
            return out
        while True:
            self.skip()
            if self.peek() != '"':
                self.fail("expected a key")
            key = self.string()
            self.skip()
            if self.peek() != ":":
                self.fail("expected a colon")
            self.pos += 1
            self.skip()
            value = self.value(depth + 1)
            if key not in out:
                out[key] = value
            self.skip()
            char = self.peek()
            if char == ",":
                self.pos += 1
                continue
            if char == "}":
                self.pos += 1
                return out
            self.fail("expected a comma or a closing brace")

    def sequence(self, depth):
        out = []
        self.pos += 1
        self.skip()
        if self.peek() == "]":
            self.pos += 1
            return out
        while True:
            self.skip()
            out.append(self.value(depth + 1))
            self.skip()
            char = self.peek()
            if char == ",":
                self.pos += 1
                continue
            if char == "]":
                self.pos += 1
                return out
            self.fail("expected a comma or a closing bracket")

    def string(self):
        self.pos += 1
        parts = []
        while True:
            if self.pos >= len(self.text):
                self.fail("unterminated string")
            char = self.text[self.pos]
            if char == '"':
                self.pos += 1
                break
            if ord(char) < 32:
                self.fail("control character in string")
            if char != "\\":
                self.pos += 1
                parts.append(char)
                continue
            self.pos += 1
            if self.pos >= len(self.text):
                self.fail("unterminated escape")
            code = self.text[self.pos]
            if code in SIMPLE_ESCAPES:
                self.pos += 1
                parts.append(SIMPLE_ESCAPES[code])
                continue
            if code != "u":
                self.fail("unknown escape")
            parts.append(self.escaped_unit())
        out = "".join(parts)
        if len(out) > MAX_STRING:
            self.fail("string too long")
        return out

    def escaped_unit(self):
        first = self.hex4()
        if 0xD800 <= first <= 0xDBFF and self.text.startswith("\\u", self.pos):
            mark = self.pos
            self.pos += 1
            second = self.hex4()
            if 0xDC00 <= second <= 0xDFFF:
                return chr(0x10000 + ((first - 0xD800) << 10) + (second - 0xDC00))
            self.pos = mark
        return chr(first)

    def hex4(self):
        self.pos += 1
        raw = self.text[self.pos:self.pos + 4]
        if len(raw) != 4:
            self.fail("short escape")
        try:
            value = int(raw, 16)
        except ValueError:
            self.fail("bad escape")
        self.pos += 4
        return value

    def number(self):
        start = self.pos
        floating = False
        if self.peek() == "-":
            self.pos += 1
        while self.peek() in DIGITS and self.peek() != "":
            self.pos += 1
        if self.peek() == ".":
            floating = True
            self.pos += 1
            while self.peek() in DIGITS and self.peek() != "":
                self.pos += 1
        if self.peek() in ("e", "E"):
            floating = True
            self.pos += 1
            if self.peek() in ("+", "-"):
                self.pos += 1
            while self.peek() in DIGITS and self.peek() != "":
                self.pos += 1
        raw = self.text[start:self.pos]
        if raw in ("", "-"):
            self.fail("bad number")
        try:
            return float(raw) if floating else int(raw)
        except ValueError:
            self.fail("bad number")


def parse(text):
    reader = Reader(text)
    reader.skip()
    result = reader.value(0)
    reader.skip()
    if reader.pos != len(reader.text):
        reader.fail("trailing data")
    return result
