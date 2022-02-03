"""Play a game of wordle."""

from __future__ import annotations

import random
import string
import sys
import time
from collections.abc import Callable
from typing import Literal, Optional

import attr
from rich.align import Align
from rich.box import HEAVY, ROUNDED, Box
from rich.layout import Layout
from rich.live import Live
from rich.markup import render
from rich.style import Style
from rich.table import Table

from wordle.getch import getch
from wordle.words import ALL_WORDS, SOLUTIONS

DARK_GRAY = "#585858"
LIGHT_GRAY = "#d7dadc"
GREEN = "#538d4e"
YELLOW = "#b59f3b"

NUM_COLS = 5
NUM_ROWS = 6

RANKS = ["Genius", "Magnificent", "Impressive", "Splendid", "Great", "Phew"]

KB_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
KB_LOCATION = {
    letter: (f"kb-row-{row_idx}", col_idx)
    for row_idx, row in enumerate(KB_ROWS)
    for col_idx, letter in enumerate(row)
}

STATE_ORDER = {
    state: order
    for order, state in enumerate(["empty", "filled", "absent", "present", "correct"])
}

StateT = Literal["empty", "filled", "absent", "present", "correct"]


@attr.mutable(order=True)
class Cell:
    """A box/cell with a single letter, used in various parts of the game."""

    _table: Table = attr.ib(cmp=False)
    state: str = attr.ib(cmp=STATE_ORDER.get)

    @classmethod
    def create(cls, letter: str, state: StateT, box: Box, bold: bool) -> Cell:
        """Return a cell with a single letter inside."""

        table = Table(box=box, show_header=False)

        match state:
            case "empty":
                table.border_style = Style(color=LIGHT_GRAY)
                table.add_row(letter, style=Style(bold=bold))
            case "filled":
                table.border_style = Style(color=LIGHT_GRAY)
                table.add_row(letter, style=Style(bold=bold))
            case "absent":
                table.border_style = Style(color=DARK_GRAY)
                table.add_row(letter, style=Style(color=DARK_GRAY, bold=bold))
            case "present":
                table.border_style = Style(color=YELLOW)
                table.add_row(letter, style=Style(color=YELLOW, bold=bold))
            case "correct":
                table.border_style = Style(color=GREEN)
                table.add_row(letter, style=Style(color=GREEN, bold=bold))

        return Cell(table=table, state=state)

    @classmethod
    def board(cls, letter: Optional[str] = None, state: StateT = "empty") -> Cell:
        """Return a game cell with a single letter inside."""
        if letter is None:
            letter = " "
        else:
            letter = letter[:1].upper()
        return cls.create(letter, state, HEAVY, True)

    @classmethod
    def keyboard(cls, letter: str, state: StateT = "empty") -> Cell:
        """Return a keyboard cell."""
        return cls.create(letter, state, ROUNDED, False)

    @property
    def letter(self) -> str:
        """Return the letter inside this cell."""
        # pylint: disable=protected-access
        return self._table.columns[0]._cells[0]

    def __rich__(self) -> str:
        """Return the rich renderable of this cell."""
        return self._table


@attr.mutable
class Game:
    """Represents a board state and solution of wordle."""

    _layout: Layout
    solution: str
    cur_row: int = attr.ib(default=0)
    cur_col: int = attr.ib(default=0)

    @classmethod
    def create(cls, solution: Optional[str] = None) -> Game:
        """Create a game that can be played."""
        if solution is None:
            solution = random.choice(SOLUTIONS)
        assert len(solution) == NUM_COLS

        layout = Layout()

        board = Table.grid()
        for _ in range(NUM_ROWS):
            board.add_row(*[Cell.board() for _ in range(NUM_COLS)])

        status = render("Start typing letters...")

        top_row = Table.grid()
        top_row.add_row(*[Cell.keyboard(let) for let in KB_ROWS[0]])
        middle_row = Table.grid()
        middle_row.add_row(*[Cell.keyboard(let) for let in KB_ROWS[1]])
        bottom_row = Table.grid()
        bottom_row.add_row(*[Cell.keyboard(let) for let in KB_ROWS[2]])

        layout.split_column(
            Layout(Align(status, "center"), name="status", size=1),
            Layout(Align(board, "center"), name="board", size=NUM_ROWS * 3),
            Layout(Align(top_row, "center"), name="kb-row-0", size=3),
            Layout(Align(middle_row, "center"), name="kb-row-1", size=3),
            Layout(Align(bottom_row, "center"), name="kb-row-2", size=3),
        )

        return Game(layout=layout, solution=solution)

    @property
    def board(self) -> Table:
        """Convenience property to get to the board of the game"""
        return self._layout["board"].renderable.renderable

    def set_status(self, text: str) -> None:
        """
        Set the status text of the game. Supports markdown. Ensure refresh is called
        after.
        """
        self._layout["status"].renderable.renderable = render(text)

    def get_cell_letter(self, row: int, col: int) -> str:
        """Get the letter of a cell."""
        # pylint: disable=protected-access
        return self.board.columns[col]._cells[row].letter

    def set_board_cell(
        self,
        row: int,
        col: int,
        letter: Optional[str] = None,
        state: StateT = "empty",
    ) -> None:
        """
        Set a cell, specified by row and col, to a certain letter in a certain state.
        """
        # pylint: disable=protected-access
        self.board.columns[col]._cells[row] = Cell.board(letter=letter, state=state)

    def set_keyboard_cell(
        self,
        letter: str,
        state: StateT,
    ) -> None:
        """
        Set a keyboard cell, specified by its letter, to a certain letter in a certain
        state.
        """
        # pylint: disable=protected-access
        new_cell = Cell.keyboard(letter=letter, state=state)
        layout_name, col_idx = KB_LOCATION[letter]
        cells = self._layout[layout_name].renderable.renderable.columns[col_idx]._cells

        if new_cell > cells[0]:
            cells[0] = new_cell

    def current_row_letters(self) -> str:
        """Get the letters of the current row, stripped of right whitespace."""
        word = "".join(
            self.get_cell_letter(self.cur_row, col) for col in range(NUM_COLS)
        )
        return word.rstrip()

    def add_letter(self, key: str, refresh_fn: Callable[[], None]) -> None:
        """Add a letter to the current row, if able."""
        if self.cur_col in [NUM_COLS - 1, NUM_COLS]:
            self.set_status("Press Enter to submit")

        if self.cur_col < NUM_COLS:
            self.set_board_cell(self.cur_row, self.cur_col, key, "filled")
            self.cur_col += 1

        refresh_fn()

    def delete_letter(self, refresh_fn: Callable[[], None]) -> None:
        """Delete a letter from the current row, if able."""
        if self.cur_col > 0:
            self.cur_col -= 1
            self.set_board_cell(self.cur_row, self.cur_col)
        else:
            self.set_status("Can't erase anymore")

        refresh_fn()

    def submit(self, refresh_fn: Callable[[], None]) -> None:
        """Submit the current row, if able. Word checking is done too."""
        if self.cur_col != NUM_COLS:
            self.set_status("Not enough letters")
            refresh_fn()
            return

        word = self.current_row_letters()
        if word not in ALL_WORDS:
            self.set_status("Not in word list")
            refresh_fn()
            return

        for idx, letter in enumerate(word):
            if letter == self.solution[idx]:
                self.set_board_cell(self.cur_row, idx, letter, "correct")
                self.set_keyboard_cell(letter, "correct")
            elif letter in self.solution:
                self.set_board_cell(self.cur_row, idx, letter, "present")
                self.set_keyboard_cell(letter, "present")
            else:
                self.set_board_cell(self.cur_row, idx, letter, "absent")
                self.set_keyboard_cell(letter, "absent")
            refresh_fn()
            if idx + 1 != NUM_COLS:
                time.sleep(0.1)

        refresh_fn()

        if word == self.solution:
            self.set_status(RANKS[self.cur_row])
            refresh_fn()
            time.sleep(3)
            sys.exit(0)
        elif self.cur_row + 1 == NUM_ROWS:
            self.set_status(f"The solution was [red]{self.solution}[/red]")
            refresh_fn()
            time.sleep(3)
            sys.exit(1)
        else:
            self.cur_col = 0
            self.cur_row += 1

    def handle_key(self, key: str, refresh_fn: Callable[[], None]) -> str:
        """Respond to a keypress by the user."""
        self.set_status("")
        match key:
            case key if key == "\x03":  # ctrl-c
                sys.exit(1)
            case key if key.upper() in string.ascii_uppercase:
                self.add_letter(key, refresh_fn)
            case key if key == "\b":
                self.delete_letter(refresh_fn)
            case key if key in "\r\n":
                self.submit(refresh_fn)
            case _:
                self.set_status("Input a valid English letter")
                refresh_fn()

    def play(self) -> None:
        """Play the game."""
        with Live(self, auto_refresh=False) as live:
            while True:
                self.handle_key(key=getch(), refresh_fn=live.refresh)

    def __rich__(self) -> str:
        """Return the rich renderable of this game."""
        return self._layout
