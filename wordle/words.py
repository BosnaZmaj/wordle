"""The solutions and allowable words of the game."""
import random
from pathlib import Path
from typing import Optional

import arrow

WORDS_PATH = Path(__file__).parent / "words.txt"
SOLUTIONS_PATH = Path(__file__).parent / "solutions.txt"


def load_words(path: Path) -> list[str]:
    """Return a list of whitespace-stripped words from each line of a file at path."""
    with path.open("r") as word_file:
        return [word.strip().upper() for word in word_file]


# this is a list, to support random.choice
SOLUTIONS = load_words(SOLUTIONS_PATH)

# this is a set, to support O(1) membership checking
ALL_WORDS = set(load_words(WORDS_PATH)) | set(SOLUTIONS)

# reference date to calculate index of word of the day. comes from the offical game.
_REFERENCE_DATE = arrow.Arrow(2021, 6, 19, tzinfo="local")


def word_of_the_day(date: Optional[arrow.Arrow] = None) -> str:
    """
    Return the solution for a given date. If date is None, return the solution for
    today.

    Note: This word is determined the same way the official game does, and can be done
    entirely offline once the solution list is known (as we have in the SOLUTIONS list):
    The word is found at an index of that list calculated by the difference, in days,
    between a reference date and the current date, modulo the size of the list.
    """
    if date is None:
        date = arrow.now()
    delta = date - _REFERENCE_DATE
    index = delta.days % len(SOLUTIONS)
    return SOLUTIONS[index]


def random_word() -> str:
    """Return a random word for the SOLUTIONS list."""
    return random.choice(SOLUTIONS)
