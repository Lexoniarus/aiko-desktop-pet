"""Immutable identities for one standard French 52-card deck."""

from dataclasses import dataclass

SUITS = ("clubs", "diamonds", "hearts", "spades")
RANKS = ("A", "02", "03", "04", "05", "06", "07", "08", "09", "10", "J", "Q", "K")


@dataclass(frozen=True, slots=True)
class Card:
    suit: str
    rank: str

    def __post_init__(self) -> None:
        if self.suit not in SUITS or self.rank not in RANKS:
            raise ValueError("Invalid playing card")

    @property
    def asset_name(self) -> str:
        return f"card_{self.suit}_{self.rank}.png"


STANDARD_DECK = tuple(Card(suit, rank) for suit in SUITS for rank in RANKS)
