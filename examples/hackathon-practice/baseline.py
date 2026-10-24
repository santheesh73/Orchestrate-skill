#!/usr/bin/env python3
"""Deliberately broken fictional baseline: drops empty request rows."""

import csv
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    with (root / 'input.csv').open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    with (root / 'output.csv').open('w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['id', 'status'])
        writer.writerows((row['id'], 'ok') for row in rows if row['request'].strip())


if __name__ == '__main__':
    main()
