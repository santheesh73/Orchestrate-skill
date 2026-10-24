#!/usr/bin/env python3
"""Complete fictional router: preserve every input, including empty requests."""

import csv
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    with (root / 'input.csv').open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    with (root / 'output.csv').open('w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['id', 'status'])
        writer.writerows((row['id'], 'ok' if row['request'].strip() else 'review') for row in rows)


if __name__ == '__main__':
    main()
