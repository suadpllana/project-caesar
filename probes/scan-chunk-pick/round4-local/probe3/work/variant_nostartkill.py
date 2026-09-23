"""Variant: no deaths at query start from what was already known (only updates/headers applied lazily)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app")); sys.path.insert(0, HERE)
import ref
