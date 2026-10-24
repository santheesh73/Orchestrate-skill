#!/usr/bin/env python3
"""Checkout entrypoint for the self-contained Orchestrate evidence companion."""

import runpy
from pathlib import Path

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      'skills/hackerrank-orchestrate-evidence/scripts/evidence.py'), run_name='__main__')
