"""Synthetic example only: a small deterministic producer, not a challenge solution."""

import csv
from pathlib import Path


def main():
    root = Path(__file__).parent
    with (root / 'input.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    with (root / 'output.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['id', 'status'])
        for row in rows:
            writer.writerow([row['id'], 'ok' if row['value'] == 'first' else 'review'])


if __name__ == '__main__':
    main()
