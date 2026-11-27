#!/usr/bin/env python3
"""news-image-20261126 entrypoint (b10, numbers, V8 two-column layout).

Copies the build-time rendered entry.png from the repository into
MAKEFUN_OUTPUT_DIR. Standard library only: the grader runs with no
network and nothing installed, so this file must not import PIL,
numpy or anything beyond os/shutil. The image itself is rendered at build time by gen.py (Pillow) and
committed as entry.png; this program only moves bytes, so both
grader runs write identical output.

Layout V8 (this entry): masthead + 2-line DATE CHECK on top; two
columns below it -- left 60% holds the tall Macy's hero over a 2x5
card grid, right 40% stacks the Hormuz and tariffs heroes over the
ALSO list; a full-width world-map strip, a thin timeline strip and
a sources footer close the page. 50 stories in total: 3 heroes,
10 cards, 37 ALSO items, 15+ regions, all of Thursday 26 Nov 2026.
"""
import hashlib
import os
import shutil
import sys


def _here():
    return os.path.dirname(os.path.abspath(__file__))


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    src = os.path.join(_here(), "entry.png")
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    dst = os.path.join(outdir, "entry.png")
    if not os.path.isfile(src):
        print("entry.png missing next to main.py", file=sys.stderr)
        return 1
    os.makedirs(outdir, exist_ok=True)
    if os.path.abspath(src) == os.path.abspath(dst):
        print("output dir is the repo dir; entry.png already in place")
    else:
        shutil.copyfile(src, dst)
    if _sha(src) != _sha(dst):
        print("copy mismatch: sha differs", file=sys.stderr)
        return 1
    size = os.path.getsize(dst)
    if size > 1048576:
        print("entry.png over 1 MiB: %d bytes" % size, file=sys.stderr)
        return 1
    print("wrote %s (%d bytes, sha256=%s)" % (dst, size, _sha(dst)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
