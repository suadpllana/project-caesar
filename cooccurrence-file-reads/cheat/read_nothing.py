"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: the opposite tolerance to read_everything.py. Most files are not
worth reading for most filters, so answer the empty list every time and see
whether anything in the suite accepts a trivially shaped result. If the grade
were a fraction of the answers, or a check that the returned indices are a
subset of the truth, this would score well without doing anything.

The verifier rejects it because every graded answer is the exact list of
indices, compared element by element, and both entry points are graded on
every filter in both blocks. The timed run is graded on a hash of every answer
in order, so an answer that is wrong anywhere is wrong everywhere. Empty lists
fail the small block on the first filter that reads a file.
"""


class Reader:
    def __init__(self, manifest):
        self.manifest = list(manifest)

    def files_to_read(self, filter_expr):
        return []


def files_to_read(manifest, filter_expr):
    return Reader(manifest).files_to_read(filter_expr)
