MODN = 2147483647


class Noise:
    def __init__(self, cfg):
        self.s = (cfg["seed"] * 7919 + 13) % MODN
        self.n = 0

    def draw(self):
        self.n += 1
        self.s = (self.s * 48271) % MODN
        return self.s

    # The state that reseeding cannot reconstruct.
    #
    # train.model takes one draw per packed row, and the number of rows a fill produces
    # depends on how the lengths happened to pack against the bin width, so the number of
    # draws taken by step k is not a function of k.  Reseeding from the seed and the step
    # counter therefore lands somewhere other than where the run was, and every gradient
    # after the load is perturbed by a different mask.  Nothing raises, the loss curve
    # looks ordinary, and the run simply never rejoins the one it continues.  The position
    # itself is the only thing that carries it, so it is saved and put back verbatim.
    def snap(self):
        return [self.s, self.n]

    def rest(self, vec):
        if len(vec) == 2:
            self.s = vec[0] % MODN
            self.n = vec[1]
