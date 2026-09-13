"""Deterministic old and revised source-manifest program families."""
import legacy_gen
import new_gen

FAMILIES = legacy_gen.FAMILIES + new_gen.FAMILIES

def programs(seed, per):
    return legacy_gen.programs(seed, per) + new_gen.programs(seed, per)
