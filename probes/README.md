Probe trajectories, kept out of the task bundles on purpose.

A trajectory is the evidence behind an easiness repair and it is the input to
`tools/leakcheck.py`. It is not part of a submission, and `share-register-screen` had
already been accepted by the pipeline when this one was written, so it lives here rather
than under `tasks/<slug>/authoring/`, where it would have changed an archive the pipeline
had passed.

One rule for these files: **the agent's own words and nothing else.** A trajectory file
that also quotes the instruction makes `leakcheck.py` circular, because the check is
looking for exactly that overlap. Commentary goes in a `notes.md` beside it.
