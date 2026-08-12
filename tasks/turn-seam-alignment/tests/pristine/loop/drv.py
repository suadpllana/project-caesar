def play(rt, ops):
    for op in ops:
        k = op["op"]
        if k == "begin":
            rt.open(op["ep"], op["salt"])
        elif k == "user":
            rt.ep(op["ep"]).user(op["text"])
        elif k == "tool":
            rt.ep(op["ep"]).tool(op["text"])
        elif k == "turn":
            rt.ep(op["ep"]).turn(op["cap"])
        elif k == "retry":
            rt.ep(op["ep"]).retry(op["text"])
        elif k == "end":
            rt.ep(op["ep"]).finish()
    return rt.report()
