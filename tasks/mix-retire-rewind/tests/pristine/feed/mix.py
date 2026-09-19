def turn(ride, slot, pass_by):
    return ride.pat[(slot - ride.base + pass_by) % len(ride.pat)]


def retire(ride, j):
    box = ride.box
    if not box.hold[j] or ride.out[j]:
        return
    if ride.ep[j] >= box.hold[j]:
        ride.out[j] = True
        ride.pat = [s for s in ride.pat if s != j]
