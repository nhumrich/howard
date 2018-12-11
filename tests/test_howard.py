from dataclasses import dataclass, field
import dataclasses
from enum import Enum
from typing import Any, List, Tuple, Dict, Union, NewType

import pytest

import howard


class Suit(Enum):
    heart = "h"
    spade = "s"
    diamond = "d"
    club = "c"


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
    def __serialize__(self):
        return {"_id": self.hand_id, "cards": howard.serialize(self.cards)}

    @classmethod
    def __deserialize__(cls, _dict):
        return cls(
            hand_id=_dict["_id"], cards=howard.deserialize(_dict["cards"], List[Card])
        )


@dataclass
class PartyWithCustomSerializationHand:
    party_id: int = 0
    players: Dict[str, CustomSerializationHand] = field(default_factory=dict)


@pytest.mark.parametrize(
    "d, t", [({"hand_id": 2, "cards": [{"rank": 2, "suit": "c"}]}, Hand)]
)
def test_dict_is_same_coming_back(d, t):
    obj = howard.deserialize(d, t)
    assert obj
    assert d == howard.serialize(obj)


def test_hand_is_what_we_expect():
    d = {"hand_id": 2, "cards": [{"rank": 2, "suit": "c"}, {"rank": 10, "suit": "h"}]}
    obj = howard.deserialize(d, Hand)

    assert isinstance(obj, Hand)
    assert obj.hand_id == 2
    assert len(obj.cards) == 2
    assert isinstance(obj.cards[0], Card)
    assert obj.cards[0].suit == Suit.club


def test_hand_without_card():
    d = {"hand_id": 1}
    obj = howard.deserialize(d, Hand)

    assert isinstance(obj, Hand)
    assert len(obj.cards) == 0


@pytest.mark.skip(reason="Not implemented")
def test_unknown_field():
    d = {"hand_i": 2}
    with pytest.raises(Exception):
        howard.deserialize(d, Hand)


def test_unsupported_type():
    with pytest.raises(TypeError):
        howard.deserialize({"n": 2}, UnsupportedFloat)


def test_float_instead_of_int():
    d = {"hand_id": 2.5}
    with pytest.raises(TypeError):
        howard.deserialize(d, Hand)


def test_unknown_suit():
    d = {"rank": 2, "suit": "a"}

    with pytest.raises(Exception):
        howard.deserialize(d, Card)


def test_dict_instead_of_list_in_hand():
    d = {"cards": {"1": {"rank": 2, "suit": "c"}}}

    with pytest.raises(TypeError):
        howard.deserialize(d, Hand)


def test_normal_dict():
    d = {"scores": {"John": 3, "Joe": -1}}
    obj = howard.deserialize(d, Score)

    assert isinstance(obj, Score)
    assert obj.scores["John"] == 3


def test_dict_of_hands():
    hand1 = {
        "hand_id": 1,
        "cards": [
            {"rank": 10, "suit": "h"},
            {"rank": 9, "suit": "s"},
            {"rank": 1, "suit": "c"},
        ],
    }
    hand2 = {
        "hand_id": 2,
        "cards": [{"rank": 2, "suit": "c"}, {"rank": 10, "suit": "h"}],
    }
    d = {"party_id": 1, "players": {"John": hand1, "Joe": hand2}}

    obj = howard.deserialize(d, Party)

    assert isinstance(obj, Party)
    assert obj.party_id == 1
    assert len(obj.players.items()) == 2
    assert "John" in obj.players.keys()
    assert isinstance(obj.players["John"], Hand)
    assert len(obj.players["John"].cards) == 3


def test_dict_of_hands():
    hand1 = {
        "hand_id": 1,
        "cards": [
            {"rank": 10, "suit": "h"},
            {"rank": 9, "suit": "s"},
            {"rank": 1, "suit": "c"},
        ],
    }
    hand2 = {
        "hand_id": 2,
        "cards": [{"rank": 2, "suit": "c"}, {"rank": 10, "suit": "h"}],
    }
    d = {"party_id": 1, "players": {"John": hand1, "Joe": hand2}}

    obj = howard.deserialize(d, Party)

    assert isinstance(obj, Party)
    assert obj.party_id == 1
    assert len(obj.players.items()) == 2
    assert "John" in obj.players.keys()
    assert isinstance(obj.players["John"], Hand)
    assert len(obj.players["John"].cards) == 3


def test_dict_of_custom_deserialization_hands():
    hand1 = {
        "_id": 1,
        "cards": [
            {"rank": 10, "suit": "h"},
            {"rank": 9, "suit": "s"},
            {"rank": 1, "suit": "c"},
        ],
    }
    hand2 = {"_id": 2, "cards": [{"rank": 2, "suit": "c"}, {"rank": 10, "suit": "h"}]}
    d = {"party_id": 1, "players": {"John": hand1, "Joe": hand2}}

    obj = howard.deserialize(d, PartyWithCustomSerializationHand)

    assert isinstance(obj, PartyWithCustomSerializationHand)
    assert obj.party_id == 1
    assert len(obj.players.items()) == 2
    assert "John" in obj.players.keys()
    assert isinstance(obj.players["John"], CustomSerializationHand)
    assert len(obj.players["John"].cards) == 3


def test_dict_of_custom_serialization_hands():
    obj = PartyWithCustomSerializationHand(
        party_id=1,
        players={
            "John": CustomSerializationHand(
                hand_id=1,
                cards=[
                    Card(rank=10, suit=Suit.heart),
                    Card(rank=9, suit=Suit.spade),
                    Card(rank=1, suit=Suit.club),
                ],
            ),
            "Joe": CustomSerializationHand(
                hand_id=2,
                cards=[Card(rank=2, suit=Suit.club), Card(rank=10, suit=Suit.heart)],
            ),
        },
    )
    hand1 = {
        "_id": 1,
        "cards": [
            {"rank": 10, "suit": "h"},
            {"rank": 9, "suit": "s"},
            {"rank": 1, "suit": "c"},
        ],
    }
    hand2 = {"_id": 2, "cards": [{"rank": 2, "suit": "c"}, {"rank": 10, "suit": "h"}]}
    d = {"party_id": 1, "players": {"John": hand1, "Joe": hand2}}
    assert howard.serialize(obj) == d

    obj = howard.deserialize(d, PartyWithCustomSerializationHand)

    assert isinstance(obj, PartyWithCustomSerializationHand)
    assert obj.party_id == 1
    assert len(obj.players.items()) == 2
    assert "John" in obj.players.keys()
    assert isinstance(obj.players["John"], CustomSerializationHand)
    assert len(obj.players["John"].cards) == 3
    assert isinstance(obj.players["John"].cards[0], Card)


@dataclass
class Person:
    name: str
    age: int

    def __serialize__(self):
        return {"type": "Person", **howard.serialize(self, as_type=dataclass)}

    @classmethod
    def __deserialize__(cls, _dict):
        return Person(**{key: value for key, value in _dict.items() if key != "type"})


def test_dict_of_as_type():
    person = Person(name="Steve", age=56)
    d = howard.serialize(person)
    assert d == {"type": "Person", "name": "Steve", "age": 56}
    assert howard.deserialize(d, Person) == person


class Workplace:
    employees: List[Person]

    def __init__(self, employees):
        self.employees = employees

    def __eq__(self, other):
        return self.employees == other.employees

    def __serialize__(self):
        return {"type": "Workplace", "employees": howard.serialize(self.employees)}

    @classmethod
    def __deserialize__(cls, _dict):
        return cls(employees=howard.deserialize(_dict["employees"], List[Person]))


def test_dict_of_non_dataclass():
    steve = Person(name="Steve", age=56)
    workplace = Workplace(employees=[steve])
    d = howard.serialize(workplace)
    assert d == {
        "type": "Workplace",
        "employees": [{"type": "Person", "name": "Steve", "age": 56}],
    }
    assert howard.deserialize(d, Workplace) == workplace


ID = NewType("ID", Union[int, str])


def test_generic_and_new_type():
    _id = ID("42")
    serialized = howard.serialize(_id)
    assert serialized == "42"
    assert howard.deserialize(serialized, ID) == "42"


from datetime import datetime


class ISODatetime(datetime):
    """
    datetime with iso serialization
    """

    @classmethod
    def __deserialize__(cls, iso_format):
        return cls.fromisoformat(iso_format)

    def __serialize__(self):
        return self.isoformat()


@dataclass(frozen=True)
class DatetimeRange:
    start: ISODatetime
    end: ISODatetime


def test_TODO_NAME():
    now = ISODatetime.now()
    serialized = howard.serialize(now)
    deserialized = howard.deserialize(serialized, Union[DatetimeRange, ISODatetime])
    assert deserialized == now

    _range = DatetimeRange(now, ISODatetime(1970, 1, 1))
    serialized = howard.serialize(_range)
    deserialized = howard.deserialize(serialized, Union[DatetimeRange, ISODatetime])
    assert deserialized == _range


def test_tuple():
    o = (1, 2)
    serialized = howard.serialize(o)
    assert serialized == (1, 2)
    deserialized = howard.deserialize(serialized, tuple)
    assert deserialized == o


def test_tuple_with_item():
    o = (
        Hand(
            hand_id=1,
            cards=[
                Card(rank=10, suit=Suit.heart),
                Card(rank=9, suit=Suit.spade),
                Card(rank=1, suit=Suit.club),
            ],
        ),
        Card(rank=2, suit=Suit.heart),
    )
    serialized = howard.serialize(o)
    assert serialized == (
        {
            "hand_id": 1,
            "cards": [
                {"rank": 10, "suit": "h"},
                {"rank": 9, "suit": "s"},
                {"rank": 1, "suit": "c"},
            ],
        },
        {"rank": 2, "suit": "h"},
    )
    deserialized = howard.deserialize(serialized, Tuple[Hand, Card])
    assert deserialized == o


def test_tuple_with_variable_items():
    o = (
        Card(rank=10, suit=Suit.heart),
        Card(rank=9, suit=Suit.spade),
        Card(rank=1, suit=Suit.club),
    )
    serializeed = howard.serialize(o)
    assert serializeed == (
        {"rank": 10, "suit": "h"},
        {"rank": 9, "suit": "s"},
        {"rank": 1, "suit": "c"},
    )
    deserialized = howard.deserialize(serializeed, Tuple[Card, ...])
    assert deserialized == o


def test_float():
    d = 12.5
    serialized = howard.serialize(d)
    assert serialized == 12.5
    deserialized = howard.deserialize(serialized, float)
    assert deserialized == d


@dataclass
class Polymorphic:
    value: Any


@dataclass
class Worker:
    name: str
    age: int
    job: str


def test_polymorphism():
    o = Worker("Steve", 36, "Programmer")
    serialized = howard.serialize(o)
    deserialized = howard.deserialize(serialized, Union[Worker, Person])
    assert deserialized == o
    deserialized = howard.deserialize(serialized, Union[Person, Worker])
    assert deserialized == o
