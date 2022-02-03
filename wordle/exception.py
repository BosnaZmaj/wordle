"""Exceptions."""


class GameplayException(Exception):
    """Base class for gameplay issues by the user."""


class NotAWordException(GameplayException):
    """That's not a word."""


class TooShortException(GameplayException):
    """Word is not the right length."""


class FullRowException(GameplayException):
    """All letter have been filled."""


class EmptyRowException(GameplayException):
    """No letters have been filled."""
