"""Authoring bench: import the sealed generator and model from the task's tests/seal."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(HERE, "..", "..", "tasks", "line-step-stop")
SEAL = os.path.normpath(os.path.join(TASK, "tests", "seal"))
APP = os.path.normpath(os.path.join(TASK, "environment", "app_src"))
SOL = os.path.normpath(os.path.join(TASK, "solution"))
# Importing from tests/seal must not leave a __pycache__ inside the bundle.
sys.dont_write_bytecode = True
sys.path.insert(0, SEAL)

import forge  # noqa: E402
import model  # noqa: E402
