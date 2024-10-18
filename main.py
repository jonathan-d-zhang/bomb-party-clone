import pathlib
import enum
import random
import selectors
import sys
import time
import string
import gzip
import json
from dataclasses import dataclass
from typing import Optional

INITIAL_LIVES = 2
MAX_LIVES = 3
WPP = 100
BOMB_TIMER = 5
# BOMB_TIMER = random.randrange(1, 5)


ALPHABET = string.ascii_lowercase

class ValidationState(enum.Enum):
    NEW_LIFE = enum.auto()
    ACCEPTED = enum.auto()
    REJECT = enum.auto()

@dataclass(frozen=True)
class Infix:
    wpp: int
    infix: str
    words: list[str]


class Ist:
    def __init__(self, infixes: list[Infix], wpp: int):
        self.infixes = [infix for infix in infixes if infix.wpp >= wpp]
        random.shuffle(self.infixes)

        self.prompts = iter(self.infixes)

    def pick_prompt(self) -> Optional[Infix]:
        try:
            return next(self.prompts)
        except StopIteration:
            return None


class BombParty:
    def __init__(
        self,
        words: list[str],
        infixes: list[Infix],
        wpp=100,
        initial_lives=2,
        max_lives=3,
    ):
        self.words = set(words)
        self.wpp = wpp
        self.lives = initial_lives
        self.max_lives = max_lives

        self.ist = Ist(infixes, wpp)

        self.used: set[str] = set()

        self.letters = set(ALPHABET)

    def validate(self, word: str, prompt: str) -> ValidationState:
        good = word not in self.used and prompt in word.lower() and word in self.words

        if good:
            self.letters.difference_update(word)
            if len(self.letters) == 0:
                self.letters = set(ALPHABET)
                if self.lives == self.max_lives:
                    return ValidationState.ACCEPTED

                self.lives += 1

                return ValidationState.NEW_LIFE
            else:
                return ValidationState.ACCEPTED
        return ValidationState.REJECT

    def next_prompt(self) -> Infix:
        if s := self.ist.pick_prompt():
            self.used.add(s.infix)
            return s

        raise ValueError("Ran out of words")

    def lose_life(self):
        self.lives -= 1
        if self.lives == 0:
            raise ValueError("Out of lives")


if __name__ == "__main__":
    dir = pathlib.Path(__file__).parent
    with gzip.open(dir / "dict.txt.gz", mode="rt") as f:
        words = f.read().lower().split("\n")  # type: ignore

    with gzip.open(dir / "ist.json.gz", mode="rt") as f:
        ist = [
            Infix(infix["wpp"], infix["infix"], infix["words"])
            for infix in json.loads(f.read().lower())
        ]

    game = BombParty(
        words, ist, wpp=WPP, initial_lives=INITIAL_LIVES, max_lives=MAX_LIVES
    )

    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)

    while True:
        infix = game.next_prompt()
        prompt = infix.infix

        print(sorted(game.letters))
        print(f"Prompt: {prompt}")
        start = time.perf_counter()
        while time.perf_counter() - start < BOMB_TIMER:
            good = False
            events = sel.select(timeout=0.01)
            state = None
            if not events:
                continue
            for _, _ in events:
                state = game.validate(input(), prompt)
                match state:
                    case ValidationState.ACCEPTED:
                        print("W")
                        break
                    case ValidationState.NEW_LIFE:
                        print("New Life !")
                        break
                    case ValidationState.REJECT:
                        print("L")

            if state != ValidationState.REJECT:
                break
        else:
            print(f"WPP: {infix.wpp}. Examples: {random.sample(infix.words, k=5)}")
            try:
                game.lose_life()
            except ValueError:
                print("you lose :(")
                sys.exit(0)
