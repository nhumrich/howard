from dataclasses import dataclass, field
import dataclasses
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict

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
class UnsupportedFloat:
    n: float


@dataclass
class CustomDateEncoding:
    start_time: datetime
    duration: timedelta

    @property
    def end_time(self):
        return self.start_time + self.duration


def test_customer_encoding_rountrip():
    d = {'start_time': '2020-02-20 20:20', 'duration': (5, 0, 0)}
    decoders = {
        datetime: lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M'),
        timedelta: lambda values: timedelta(*values)
    }
    encoders = {
        datetime: lambda ts: ts.strftime('%Y-%m-%d %H:%M'),
        timedelta: lambda td: (td.days, td.seconds, td.microseconds)
    }
    obj = howard.from_dict(d, CustomDateEncoding, decoders=decoders)
    d_new = howard.to_dict(obj, encoders=encoders)
    assert isinstance(obj.start_time, datetime)
    assert isinstance(obj.duration, timedelta)
    assert obj.end_time == datetime(2020, 2, 25, 20, 20)
    assert d == d_new


def test_custom_float_roundtrip():
    d = {'n': 5.0}
    decoders = {float: lambda x: x}
    encoders = {float: lambda x: x}
    obj = howard.from_dict(d, UnsupportedFloat, decoders=decoders)
    d_new = howard.to_dict(obj, encoders=encoders)
    assert obj.n == 5.0
    assert d_new == d


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
    assert isinstance(obj.cards[0], Card)
    assert obj.cards[0].suit == Suit.club


def test_hand_without_card():
    d = {'hand_id': 1}
    obj = howard.from_dict(d, Hand)

    assert isinstance(obj, Hand)
    assert len(obj.cards) == 0


def test_unsupported_type():
    with pytest.raises(TypeError):
        howard.from_dict({'n': 2}, UnsupportedFloat)


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

