"""Run the local toolkit with python -m orchestrate_toolkit."""

import sys

from .cli import main

if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='backslashreplace')
    sys.exit(main())
