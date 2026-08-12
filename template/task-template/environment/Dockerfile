FROM ubuntu:24.04

# The agent's environment. Everything the task legitimately needs goes here.
#
# RULES:
#   - NEVER COPY anything from ../tests/ or ../solution/ into this image.
#     Ground truth, expected outputs, and the reference solution must not be reachable
#     by the agent. This is the single most common way a task is silently broken.
#   - Pin every Python package with == (e.g. pip install numpy==2.1.3).
#   - Do NOT pin apt packages.
#   - Make the image reproducible: no "latest" tags, no unpinned installs.

# Example:
# RUN apt-get update && apt-get install -y \
#         build-essential \
#         git \
#     && rm -rf /var/lib/apt/lists/*

# Example (note the == pins):
# RUN pip install --no-cache-dir \
#         numpy==2.1.3 \
#         pandas==2.2.3

# THE PROJECT TREE — this is where the task's difficulty lives (docs/DIFFICULTY.md, Prong B).
# Most tasks should drop the agent into a realistic project, not an empty /app: many files,
# nested modules, real couplings — the constraint in one module, its consumer in another,
# config indirection deciding which code path is live. The correct plan should only be
# formable by exploring and correlating across the tree.
#
# Keep the tree in environment/app_src/ and copy it in:
# COPY app_src/ /app/
#
# Discipline: every directory should carry at least one fact the correct plan depends on.
# A tree that could be flattened without changing the plan is bulk, not difficulty —
# and a gratuitous maze fails the quality review as an artificial handicap.
#
# Write app_src/ code the way real production code is written: sparse. No explanatory
# comments, docstrings, or architecture READMEs — explanation hands the plan over. Missing
# and stale docs are realistic; FALSE docs are a trap and fail review. (This applies to the
# agent's code only — tests/ must stay well-commented.)

# Copy any starting data the agent needs.
# COPY data/ /app/data/

WORKDIR /app
