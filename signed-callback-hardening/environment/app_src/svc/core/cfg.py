import os
import tomllib
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent / "conf" / "profiles"

_loaded = {}


def active_profile():
    return os.environ.get("SVC_PROFILE", "standard")


def load():
    name = active_profile()
    if name not in _loaded:
        path = PROFILE_DIR / (name + ".toml")
        with open(path, "rb") as handle:
            _loaded[name] = tomllib.load(handle)
    return _loaded[name]


def section(name):
    return load().get(name, {})
