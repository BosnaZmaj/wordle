"""Play a game of wordle."""

from __future__ import annotations

import string
import sys
import time
from collections.abc import Callable
from typing import Literal

import attr
from rich.align import Align
from rich.box import HEAVY, ROUNDED, Box
from rich.console import RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.markup import render
from rich.style import Style
from rich.table import Table

from wordle.exception import (
    EmptyRowException,
    FullRowException,
    NotAWordException,
    TooShortException,
)
from wordle.getch import getch
from wordle.words import ALL_WORDS

DARK_GRAY = "#585858"
LIGHT_GRAY = "#d7dadc"
GREEN = "#538d4e"
YELLOW = "#b59f3b"

NUM_COLS = 5
NUM_ROWS = 6

RANKS = ["Genius", "Magnificent", "Impressive", "Splendid", "Great", "Phew"]

KB_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

STATE_ORDER = {
    state: order
    for order, state in enumerate(["empty", "filled", "absent", "present", "correct"])
}

StateT = Literal["empty", "filled", "absent", "present", "correct"]


@attr.mutable(order=True, kw_only=True)
class Cell:
    """A box/cell with a single letter, used in various parts of the game."""

    letter: str = attr.ib(default=" ", cmp=False)
    state: StateT = attr.ib(default="empty", cmp=STATE_ORDER.get)

    def _renderable(self, box: Box, bold: bool) -> RenderableType:
        """Return the rich renderable of this cell."""
        table = Table(box=box, show_header=False)

        match self.state:
            case "empty":
                border_style = Style(color=LIGHT_GRAY)
                text_style = Style(bold=bold)
            case "filled":
                border_style = Style(color=LIGHT_GRAY)
                text_style = Style(bold=bold)
            case "absent":
                border_style = Style(color=DARK_GRAY)
                text_style = Style(color=DARK_GRAY, bold=bold)
            case "present":
                border_style = Style(color=YELLOW)
                text_style = Style(color=YELLOW, bold=bold)
            case "correct":
                border_style = Style(color=GREEN)
                text_style = Style(color=GREEN, bold=bold)

        table.border_style = border_style
        table.add_row(self.letter, style=text_style)

        return table

    def board_renderable(self) -> RenderableType:
        """Return a game cell with a single letter inside."""
        return self._renderable(HEAVY, True)

    def keyboard_renderable(self) -> RenderableType:
        """Return a keyboard cell."""
        return self._renderable(ROUNDED, False)

    def __str__(self) -> str:
        return self.letter


@attr.mutable(kw_only=True)
class BoardRow:
    """Represents 1 row of the board."""

    cells: list[Cell] = attr.ib(factory=lambda: [Cell() for _ in range(NUM_COLS)])
    input_index: int = attr.ib(default=0)

    def submit(self, solution: str) -> list[Cell]:
        """
        Checks these cells against the letters of solution and return if everything is
        correct. Raises exceptions if the current word is too short or not a valid word.
        """
        word = str(self).rstrip()
        if len(word) < NUM_COLS:
            raise TooShortException()
        if word not in ALL_WORDS:
            raise NotAWordException()

        new_cells = []

        for idx, letter in enumerate(word):
            if letter == solution[idx]:
                new_cell = Cell(letter=letter, state="correct")
            elif letter in solution:
                new_cell = Cell(letter=letter, state="present")
            else:
                new_cell = Cell(letter=letter, state="absent")
            new_cells.append(new_cell)

        return new_cells

    @property
    def correct(self) -> bool:
        """Returns if the row's cells are all correct"""
        return all(cell.state == "correct" for cell in self.cells)

    def add_letter(self, letter: str) -> None:
        """
        Adds a letter to the current row, if able. Raises exception if no room is left.
        """

        if self.input_index == NUM_COLS:
            raise FullRowException()

        self.cells[self.input_index] = Cell(letter=letter.upper(), state="filled")
        self.input_index += 1

    def delete_letter(self) -> None:
        """
        Deletes a letter from the current row, if able. Raises exception there are no
        letters to delete.
        """

        if self.input_index == 0:
            raise EmptyRowException()

        self.input_index -= 1
        self.cells[self.input_index] = Cell()

    def __str__(self) -> str:
        return "".join(str(cell) for cell in self.cells)


@attr.mutable(kw_only=True)
class Board:
    """The area where letters are input and checked against the solution."""

    rows: list[BoardRow] = attr.ib(
        factory=lambda: [BoardRow() for _ in range(NUM_ROWS)]
    )
    active_row_index: int = attr.ib(default=0)

    def submit(self, solution: str) -> list[Cell]:
        """
        Return a list of cells of the board's active row with states updated according
        to the solution.
        """
        checked_cells = self.rows[self.active_row_index].submit(solution)
        self.active_row_index += 1
        return checked_cells

    def add_letter(self, letter: str) -> None:
        """Add a letter to the board's active row."""
        return self.active_row.add_letter(letter)

    def delete_letter(self) -> None:
        """Delete a letter from the board's active row."""
        return self.active_row.delete_letter()

    @property
    def active_row(self) -> BoardRow:
        """The current row the user is inputting into."""
        return self.rows[self.active_row_index]

    @property
    def submitted_row(self) -> BoardRow:
        """The row the user just submitted."""
        return self.rows[self.active_row_index - 1]

    def layout(self) -> Layout:
        """A rich layout representing this board."""
        board = Table.grid()
        for row in self.rows:
            board.add_row(*(cell.board_renderable() for cell in row.cells))
        return Layout(Align.center(board), name="board", size=3 * NUM_ROWS)


def _default_kb_cells() -> dict[str, Cell]:
    cells_by_letter = {}
    for row in KB_ROWS:
        for letter in row:
            cells_by_letter[letter] = Cell(letter=letter)
    return cells_by_letter


@attr.mutable(kw_only=True)
class Keyboard:
    """
    A status area that shows how each letter of the alphabet has been applied towards
    the solution.
    """

    cells_by_letter: dict[str, Cell] = attr.ib(factory=_default_kb_cells)

    def update(self, cell: Cell) -> None:
        """Update the keyboard with the state of cell."""
        self.cells_by_letter[cell.letter] = max(cell, self.cells_by_letter[cell.letter])

    def layout(self) -> Layout:
        """A rich layout representing this keyboard."""
        layout = Layout(size=3 * 3)

        for kb_row in KB_ROWS:
            table = Table.grid()
            table.add_row(
                *(
                    self.cells_by_letter[letter].keyboard_renderable()
                    for letter in kb_row
                )
            )
            layout.add_split(Layout(Align.center(table), size=3))

        return layout


@attr.mutable(kw_only=True)
class Status:
    """An area to communicate messages to the user."""

    text: str = attr.ib(
        default=(
            "Welcome to Wordle! Type letters to make a word, Enter to submit, and "
            "Ctrl-C to quit."
        )
    )

    def set(self, new_text: str) -> None:
        """Change the status text. rich markup is supported."""
        self.text = new_text

    def clear(self) -> None:
        """Clear the status text."""
        self.text = ""

    def layout(self) -> Layout:
        """A rich layout representing this status."""
        return Layout(Align.center(render(self.text)), size=1, name="status")


@attr.mutable
class Game:
    """Represents a board state and solution of wordle."""

    solution: str
    status: Status = attr.ib(factory=Status)
    board: Board = attr.ib(factory=Board)
    keyboard: Keyboard = attr.ib(factory=Keyboard)

    def submit(self, refresh_fn: Callable[[], None]) -> None:
        """
        Update the board's submitted row with cells that have been checked against the
        solution. This method sleep's to create the effect of animation.

        If the solution was found or attempts exhausted, display an appropriate status
        and then quit the program.

        If there's an issue, set an appropriate status.
        """
        try:
            checked_cells = self.board.submit(self.solution)
        except TooShortException:
            self.status.set("Not enough letters")
            return
        except NotAWordException:
            self.status.set("Not in word list")
            return

        for cell_idx, checked_cell in enumerate(checked_cells):
            self.board.submitted_row.cells[cell_idx] = checked_cell
            self.keyboard.update(checked_cell)
            time.sleep(0.1)
            refresh_fn()

        if self.board.submitted_row.correct:
            self.status.set(RANKS[self.board.active_row_index - 1])
            refresh_fn()
            time.sleep(2)
            sys.exit(1)
        elif self.board.active_row_index == NUM_ROWS:
            self.status.set(f"Correct word was [red]{self.solution}[/red]")
            refresh_fn()
            time.sleep(2)
            sys.exit(1)

    def add_letter(self, letter: str) -> None:
        """Add a letter, or set an appropriate status."""
        try:
            self.board.add_letter(letter)
        except FullRowException:
            self.status.set("Press Enter to submit")

    def delete_letter(self) -> None:
        """Delete a letter, or set an appropriate status."""
        try:
            self.board.delete_letter()
        except EmptyRowException:
            self.status.set("Can't erase anymore")

    def handle_key(self, key: str, refresh_fn: Callable[[], None]) -> str:
        """Respond to a keypress by the user."""
        self.status.clear()

        match key:
            case key if key == "\x03":  # ctrl-c
                sys.exit(1)
            case key if key.upper() in string.ascii_uppercase:
                self.add_letter(key)
            case key if key == "\b":
                self.delete_letter()
            case key if key in "\r\n":
                self.submit(refresh_fn)
            case _:
                self.status.set("Input a valid English letter")

        # if no other status has been set, set to these help messages
        if not self.status.text:
            if (
                self.board.active_row.input_index == 0
                and self.board.active_row_index == 0
            ):
                self.status.set("Enter some letters...")
            elif self.board.active_row.input_index == NUM_COLS:
                self.status.set("Press Enter to submit")

    def play(self) -> None:
        """Play the game."""
        with Live(self, auto_refresh=False) as live:
            while True:
                self.handle_key(key=getch(), refresh_fn=live.refresh)
                live.refresh()

    def __rich__(self) -> RenderableType:
        """Return the rich renderable of this game."""

        layout = Layout()
        layout.split_column(
            self.status.layout(),
            self.board.layout(),
            self.keyboard.layout(),
        )
        return layout
