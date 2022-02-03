"""The solutions and allowable words of the game."""
from pathlib import Path

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
