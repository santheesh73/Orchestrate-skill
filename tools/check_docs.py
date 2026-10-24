#!/usr/bin/env python3
"""Check local Markdown destinations and heading anchors without network access.

Failure it prevents: documentation that points to missing local files or sections.
External links are reported as unchecked, not treated as verified successful URLs.
"""

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def anchors(path):
    counts, result, fenced = {}, set(), False
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        if fenced or not re.match(r'^#{1,6} ', line):
            continue
        heading = re.sub(r'^#+ ', '', line).strip().lower().replace('`', '')
        slug = re.sub(r'[^\w\- ]', '', heading).replace(' ', '-')
        index = counts.get(slug, 0)
        result.add(slug + ('-' + str(index) if index else ''))
        counts[slug] = index + 1
    return result


def check(root, paths):
    errors, local, external = [], 0, set()
    for name in paths:
        source = root / name
        source.resolve().relative_to(root.resolve())
        for link in re.findall(r'\]\(([^)\n]+)\)', source.read_text(encoding='utf-8-sig')):
            link = link.strip().strip('<>')
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                external.add(link)
                continue
            target = (source.parent / unquote(parts.path)).resolve() if parts.path else source
            try:
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(str(name) + ': link leaves repository: ' + link)
                continue
            if not target.exists():
                errors.append(str(name) + ': missing file: ' + link)
            elif parts.fragment and target.suffix == '.md' and unquote(parts.fragment) not in anchors(target):
                errors.append(str(name) + ': missing anchor: ' + link)
            local += 1
    return {'local_links': local, 'external_unchecked': len(external), 'errors': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='repository-relative Markdown files; defaults to README and docs')
    args = parser.parse_args(argv)
    paths = args.paths or ['README.md'] + [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'docs').rglob('*.md'))]
    try:
        result = check(ROOT, paths)
    except (OSError, ValueError) as exc:
        print('Documentation check refused: ' + type(exc).__name__)
        return 2
    for error in result['errors']:
        print('ERROR ' + error)
    print('Local links: %d; external URLs unchecked: %d; errors: %d' %
          (result['local_links'], result['external_unchecked'], len(result['errors'])))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
