from dataclasses import dataclass, field
import dataclasses
from enum import Enum
from typing import List

import pytest

import howard


class Suit(Enum):
    heart = 'h'
    spade = 's'
    diamond = 'd'
    club = 'c'


@dataclass
class Card:
    rank: int
    suit: Suit


@dataclass
class Hand:
    hand_id: int = 0
    cards: List[Card] = field(default_factory=list)


@pytest.mark.parametrize('d, t', [
    ({'hand_id': 2, 'cards': [{'rank': 2, 'suit': 'c'}]}, Hand),
])
def test_dict_is_same_coming_back(d, t):
    obj = howard.from_dict(d, t)
    assert obj
    assert d == howard.to_dict(obj)


def test_hand_is_what_we_expect():
    d = {'hand_id': 2, 'cards': [{'rank': 2, 'suit': 'c'}, {'rank': 10, 'suit': 'h'}]}
    obj = howard.from_dict(d, Hand)

    assert isinstance(obj, Hand)
    assert obj.hand_id == 2
    assert len(obj.cards) == 2
    assert obj.cards[0].suit == Suit.club
