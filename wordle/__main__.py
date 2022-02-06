"""Main module entry point"""
from typing import Optional

import arrow
import click

from wordle.game import Game
from wordle.words import random_word, word_of_the_day


@click.command()
@click.option(
    "--date",
    "date_str",
    default="random",
    show_default=True,
    help=(
        "Play with the solution of the specified date. If the date given is the string "
        '"today", then play with today\'s word. If the string "random" is given, play '
        "with a random word. Otherwise, attempt to parse the date and play with the "
        "word of that date."
    ),
)
def main(date_str: Optional[str]) -> None:
    """Play a game of Wordle."""
    match date_str:
        case "today":
            solution = word_of_the_day()
        case "random":
            solution = random_word()
        case _:
            try:
                date = arrow.get(date_str)
            except arrow.parser.ParserError as parser_error:
                raise click.BadArgumentUsage(parser_error)
            solution = word_of_the_day(date=date)
    Game(solution=solution).play()


if __name__ == "__main__":
    main.main()
