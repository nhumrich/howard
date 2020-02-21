from dataclasses import dataclass, field
import dataclasses
from enum import Enum
from typing import List, Dict, Tuple

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


@dataclass
class Party:
    party_id: int = 0
    players: Dict[str, Hand] = field(default_factory=dict)


@dataclass
class Score:
    scores: Dict[str, int] = field(default_factory=dict)


@dataclass
class Measurement:
    units: str
    value: float


@dataclass
class UnsupportedTuple:
    t: Tuple


@pytest.mark.parametrize('d, t', [
    ({'hand_id': 2, 'cards': [{'rank': 2, 'suit': 'c'}]}, Hand),
    ({'units': 'kg', 'value': 5.0}, Measurement),
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
    assert isinstance(obj.cards[0], Card)
    assert obj.cards[0].suit == Suit.club


def test_hand_without_card():
    d = {'hand_id': 1}
    obj = howard.from_dict(d, Hand)

    assert isinstance(obj, Hand)
    assert len(obj.cards) == 0


def test_unsupported_type():
    with pytest.raises(TypeError):
        howard.from_dict({'t': (1, 2, 3)}, UnsupportedTuple)


def test_float_instead_of_int():
    d = {'hand_id': 2.5}
    with pytest.raises(TypeError):
        howard.from_dict(d, Hand)


def test_unknown_suit():
    d = {'rank': 2, 'suit': 'a'}

    with pytest.raises(Exception):
        howard.from_dict(d, Card)


def test_dict_instead_of_list_in_hand():
    d = {'cards': {'1': {'rank': 2, 'suit': 'c'}}}

    with pytest.raises(TypeError):
        howard.from_dict(d, Hand)


def test_normal_dict():
    d = {'scores': {'John': 3, 'Joe': -1}}
    obj = howard.from_dict(d, Score)

    assert isinstance(obj, Score)
    assert obj.scores['John'] == 3


def test_dict_of_hands():
    hand1 = {'hand_id': 1, 'cards': [{'rank': 10, 'suit': 'h'}, {'rank': 9, 'suit': 's'}, {'rank': 1, 'suit': 'c'}]}
    hand2 = {'hand_id': 2, 'cards': [{'rank': 2, 'suit': 'c'}, {'rank': 10, 'suit': 'h'}]}
    d = {'party_id': 1, 'players': {'John': hand1, 'Joe': hand2}}

    obj = howard.from_dict(d, Party)

    assert isinstance(obj, Party)
    assert obj.party_id == 1
    assert len(obj.players.items()) == 2
    assert 'John' in obj.players.keys()
    assert isinstance(obj.players['John'], Hand)
    assert len(obj.players['John'].cards) == 3

def test_strip_out_public():
    @dataclass
    class Test2:
        a: int
        b: str
        _c: str

    t = Test2(a=1, b='2', _c='3')
    result = howard.to_dict(t, public_only=True)

    assert result.get('a') == 1
    assert result.get('b') == '2'
    assert '_c' not in result

def test_strip_out_internal_fields():
    @dataclass
    class Test3:
        a: int
        b: str = field(default='', metadata={'internal': True})

    t = Test3(a=1, b='3')
    result = howard.to_dict(t)
    assert 'b' not in result

