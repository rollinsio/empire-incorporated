"""Named, independent random streams.

Each part of the generator draws from its own stream, so adding documents in
one module never reshuffles the people, codes or numbers produced by another.
String seeds are hashed with SHA-512 by ``random.Random``, which is stable
across processes and unaffected by ``PYTHONHASHSEED``.
"""

import random

from generator.config import SEED


def stream(name: str) -> random.Random:
    return random.Random(f"{SEED}:{name}")
