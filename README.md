# Tim's Wordle Clone

Practice [Wordle](https://www.powerlanguage.co.uk/wordle/) from the command line with a random
official word. No internet required!

![Demonstration of the program](docs/demo.gif)

## Installation

Ensure you have Python >= 3.10.

```shell
git clone https://github.com/t-mart/wordle.git
pip install --user wordle/  # or pipx, or virtualenv, or whatever
```

Then, run it with:

```shell
wordle
```

## Words

The words used in this game come from the actual [Wordle](https://www.powerlanguage.co.uk/wordle/)
application itself.

- [`solutions.txt`](wordle/solutions.txt) contains words which can be used as solutions.
- [`words.txt`](wordle/words.txt) contains other valid English words that are recognized in tries.
  (These words are less common like "fuzil", "sewin", and "tolan", but are still helpful in deducing
  solutions.)
