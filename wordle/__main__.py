"""Main module entry point"""
from wordle.game import Game


def main() -> None:
    """Create and play a game"""
    game = Game.create()
    game.play()


if __name__ == "__main__":
    main()
