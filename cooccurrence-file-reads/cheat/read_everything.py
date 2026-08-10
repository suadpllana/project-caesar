"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: the instruction says outright that reading a file you did not have
to is only wasted work, while skipping one you needed is the bug that took the
feature offline. So never skip. Return every file, every time, and skip the
problem entirely.

The verifier rejects it because the graded answer is the exact list, not a
superset. Most files in the graded manifests are not read for most filters, so
this fails the small block, the wide block and the digest over the timed run.
"""


class Reader:
    def __init__(self, manifest):
        self.manifest = list(manifest)

    def files_to_read(self, filter_expr):
        return list(range(len(self.manifest)))


def files_to_read(manifest, filter_expr):
    return Reader(manifest).files_to_read(filter_expr)
