"""
Cross-platform stdin character getting.

From: https://stackoverflow.com/a/510364/235992
"""
# pylint: disable=import-error

import platform

if platform.system() == "Windows":
    import msvcrt

    def getch() -> str:
        """Return the next character of input."""
        return msvcrt.getch().decode("utf-8")

else:
    import sys
    import termios
    import tty

    def getch() -> str:
        """Return the next character of input."""
        file_desc = sys.stdin.fileno()
        old_settings = termios.tcgetattr(file_desc)
        try:
            tty.setraw(file_desc)
            character = sys.stdin.read(1)
        finally:
            termios.tcsetattr(file_desc, termios.TCSADRAIN, old_settings)
        return character
