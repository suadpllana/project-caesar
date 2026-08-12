#!/bin/bash
# Verifier entry point. Runs in a SEPARATE container built from tests/Dockerfile, which
# owns /tests and has ALL tooling baked in at build time (pytest and its CTRF plugin are
# installed in the Dockerfile, at the canonical pins).
#
# STRICT: nothing here may touch the network or install anything. No curl, no wget, no
# pip/apt/uv at trial time — the platform rejects verifier network fetches and trial-time
# tooling installs as blocking errors. If the tests need another dependency, add it to
# tests/Dockerfile with a == pin.
#
# What this container can see of the agent's work: exactly the paths declared in
# `artifacts` in task.toml, re-materialized at their ORIGINAL absolute paths
# (the agent's /app/output.json is read here as /app/output.json). Nothing else.
#
# Contract, which must not change:
#   - Write exactly `0` or `1` to /logs/verifier/reward.txt
#   - Emit a pytest CTRF report to /logs/verifier/ctrf.json

pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
