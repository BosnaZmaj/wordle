"""Main module entry point"""
from wordle.game import Game


def main() -> None:
    """Create and play a game"""
    Game().play()


if __name__ == "__main__":
    main()
