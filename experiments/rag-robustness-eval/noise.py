"""Noise injection functions for corrupting retrieval corpus documents."""

import random
import string


def char_noise(text: str, rate: float, seed: int = 42) -> str:
    """Replace random alphabetic characters with random lowercase letters."""
    rng = random.Random(seed)
    chars = list(text)
    for i, ch in enumerate(chars):
        if ch.isalpha() and rng.random() < rate:
            chars[i] = rng.choice(string.ascii_lowercase)
    return "".join(chars)


def word_drop(text: str, rate: float, seed: int = 42) -> str:
    """Randomly drop words at the given rate (0 = keep all, 1 = drop all)."""
    rng = random.Random(seed)
    words = text.split()
    kept = [w for w in words if rng.random() > rate]
    return " ".join(kept) if kept else words[0]


def truncate(text: str, fraction: float) -> str:
    """Keep only the first fraction of the text by character count."""
    if fraction >= 1.0:
        return text
    cutoff = max(1, int(len(text) * fraction))
    return text[:cutoff]
