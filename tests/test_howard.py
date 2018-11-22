from dataclasses import dataclass, field
import dataclasses
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
class CustomSerializationHand(Hand):
    def to_dict(self):
        return {
            '_id': self.hand_id,
            'cards': list(map(howard.to_dict, self.cards))
        }

    @classmethod
    def from_dict(cls, _dict):
        return cls(hand_id=_dict['_id'], cards=[
            howard.from_dict(card_dict, Card)
            for card_dict
            in _dict['cards']
        ])


@dataclass
class PartyWithCustomSerializationHand:
    party_id: int = 0
    players: Dict[str, CustomSerializationHand] = field(default_factory=dict)


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


@pytest.mark.skip(reason="Not implemented")
def test_unknown_field():
    d = {'hand_i': 2}
    with pytest.raises(Exception):
        howard.from_dict(d, Hand)


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


def test_dict_of_custom_serialization_hands():
    hand1 = {'_id': 1, 'cards': [{'rank': 10, 'suit': 'h'}, {'rank': 9, 'suit': 's'}, {'rank': 1, 'suit': 'c'}]}
    hand2 = {'_id': 2, 'cards': [{'rank': 2, 'suit': 'c'}, {'rank': 10, 'suit': 'h'}]}
    d = {'party_id': 1, 'players': {'John': hand1, 'Joe': hand2}}

    obj = howard.from_dict(d, PartyWithCustomSerializationHand)

    assert isinstance(obj, PartyWithCustomSerializationHand)
    assert obj.party_id == 1
    assert len(obj.players.items()) == 2
    assert 'John' in obj.players.keys()
    assert isinstance(obj.players['John'], CustomSerializationHand)
    assert len(obj.players['John'].cards) == 3