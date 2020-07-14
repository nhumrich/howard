from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from typing import List, Dict, Tuple, Optional, Sequence, Union, TypedDict, Literal

import pytest

import howard


class Suit(Enum):
    heart = 'h'
    spade = 's'
    diamond = 'd'
    club = 'c'


def validate_rank(i: int) -> int:
    lb, ub = 1, 13
    if lb <= i <= ub:
        return i
    raise ValueError(f'{i} is not between {lb} and {ub}')


@dataclass
class Card:
    rank: int = field(metadata=dict(howard=dict(decoder=validate_rank)))
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


@dataclass
class Drink:
    name: str
    glass_type: Optional[str] = field(default=None)


@dataclass
class UnsupportedFloat:
    n: float


@dataclass
class Inner:
    val: str


@dataclass
class Outer:
    inner: Inner


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


def test_extra_fields_are_ignored():
    d = {'rank': 2, 'suit': 'h', 'exta': 'foo'}
    obj = howard.from_dict(d, Card)
    assert isinstance(obj, Card)
    assert obj.rank == 2
    assert not hasattr(obj, 'extra')


def test_nested_extra_fields_are_ignored():
    d = {'inner': {'val': 'inner_value', 'extra': 'foo'}}
    obj = howard.from_dict(d, Outer)
    assert isinstance(obj, Outer)
    assert isinstance(obj.inner, Inner)
    assert not hasattr(obj.inner, 'extra')


def test_listed_extra_fields_are_ignored():
    d = {
            'hand_id': 2, 'cards': [
                {'rank': 10, 'suit': 'h', 'extra': 'foo'}
            ]
        }
    obj = howard.from_dict(d, Hand)
    assert isinstance(obj, Hand)
    assert obj.cards[0].rank == 10
    assert not hasattr(obj.cards[0], 'extra')


def test_extra_dict_value_fields_are_ignored():
    d = {
        'party_id': 1,
        'players': {'John': {'hand_id': 2, 'cards': [], 'extra': 'foo'}}
    }
    obj = howard.from_dict(d, Party)
    assert isinstance(obj, Party)
    assert not hasattr(obj.players['John'], 'extra')


def test_extra_fields_raise():
    d = {'rank': 2, 'suit': 'h', 'extra': 'foo'}
    with pytest.raises(TypeError):
        howard.from_dict(d, Card, ignore_extras=False)


def test_nested_extra_fields_raise():
    d = {'inner': {'val': 'inner_value', 'extra': 'foo'}}
    with pytest.raises(TypeError):
        howard.from_dict(d, Outer, ignore_extras=False)


def test_listed_extra_fields_raise():
    d = {
            'hand_id': 2, 'cards': [
                {'rank': 10, 'suit': 'h', 'extra': 'foo'}
            ]
        }
    with pytest.raises(TypeError):
        howard.from_dict(d, Hand, ignore_extras=False)


def test_extra_dict_value_fields_raise():
    d = {
        'party_id': 1,
        'players': {'John': {'hand_id': 2, 'cards': [], 'extra': 'foo'}}
    }
    with pytest.raises(TypeError):
        howard.from_dict(d, Party, ignore_extras=False)


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


def test_optional_type_not_set():
    drink = {'name': 'tequila'}
    obj = howard.from_dict(drink, Drink)
    assert isinstance(obj, Drink)
    assert obj.glass_type is None
    # TODO: currently disabled as None is not a supported exportable type
    # assert {'name': 'tequila', 'glass_type': None} == howard.to_dict(obj)


def test_optional_type_set():
    drink = {'name': 'scotch', 'glass_type': 'lowball'}
    obj = howard.from_dict(drink, Drink)
    assert isinstance(obj, Drink)
    assert 'lowball' == obj.glass_type
    assert {'name': 'scotch', 'glass_type': 'lowball'} == howard.to_dict(obj)


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


def test_field_validation():
    data = {'suit': 'h', 'rank': 20}
    with pytest.raises(ValueError):
        howard.from_dict(data, Card)


def test_custom_field_decoding():
    def decode_date(s: str) -> date:
        return date.fromisoformat(s)

    @dataclass
    class Person:
        name: str
        dob: date = field(metadata=dict(howard=dict(decoder=decode_date)))

    data = {'name': 'Bob', 'dob': '2020-01-01'}
    expected_dob = date(2020, 1, 1)
    bob = howard.from_dict(data, Person)

    assert bob.dob == expected_dob


def test_custom_field_encoding():
    def encode_date(d: date) -> str:
        return d.isoformat()

    @dataclass
    class Person:
        name: str
        dob: date = field(metadata=dict(howard=dict(encoder=encode_date)))

    bob = Person(name='Bob', dob=date(2020, 1, 1))

    expected_dob = '2020-01-01'
    data = howard.to_dict(bob)

    assert data['dob'] == expected_dob


def test_multipart_field_encoding_decoding():
    def seq_to_date(s: Sequence[int]) -> date:
        year, month, day = s
        return date(year, month, day)

    def date_to_seq(d: date) -> Sequence:
        return (d.year, d.month, d.day)

    date_field = field(
        metadata=dict(howard=dict(decoder=seq_to_date, encoder=date_to_seq))
    )

    @dataclass
    class Person:
        name: str
        dob: date = date_field

    data = {'name': 'Alice', 'dob': (2020, 1, 15)}
    expected_dob = date(2020, 1, 15)
    alice = howard.from_dict(data, Person)
    assert alice.dob == expected_dob
    # Test roundtrip:
    assert howard.to_dict(alice) == data


def test_none_with_none_as_default():

    @dataclass
    class ProcMan:
        schedule: Union[str, None] = field(default=None)
        children_ids: List[str] = field(default_factory=list)
        node_context: dict = field(default_factory=dict)
    config = {'children_ids': []}
    process_config = howard.from_dict(config, ProcMan)

    # This would cause an error if a default value is actually "none
    howard.to_dict(process_config)


def test_datetime_to_from_dict():

    @dataclass
    class DateTimeTest:
        my_date: datetime

    data = {'my_date': '1994-11-05T13:15:30Z'}
    # marshal into DateTimeTest object
    test_datetime = howard.from_dict(data, DateTimeTest)
    # make sure it is a datetime and the right year (should be right beyond that)
    assert type(test_datetime.my_date) is datetime
    assert test_datetime.my_date.year == 1994

    # Then go back to a dict and make sure we didn't lose any data for the datetime.
    new_dict = howard.to_dict(test_datetime)
    assert '1994-11-05T13:15:30' in new_dict.get('my_date')


def test_with_typed_dict():
    @dataclass
    class TypedDictTest:
        sub: List[TypedDict('sub', {'key1': str, 'key2': int})]

    data = {'sub': [{'key1': 'hello', 'key2': 5}]}
    result = howard.from_dict(data, TypedDictTest)
    assert isinstance(result, TypedDictTest)
    assert isinstance(result.sub, list)
    assert isinstance(result.sub[0], dict)

    test_dict = howard.to_dict(result)
    assert isinstance(test_dict, dict)
    assert isinstance(test_dict['sub'], list)


def test_with_typed_dict_fail():
    @dataclass
    class TypedDictTest:
        sub: List[TypedDict('sub', {'key1': str, 'key2': int})]

    data = {'sub': [{'key1': 'hello'}]}
    with pytest.raises(TypeError):
        howard.from_dict(data, TypedDictTest)


def test_with_typed_dict_total_false():
    @dataclass
    class TypedDictTest:
        sub: List[TypedDict('sub', {'key1': str, 'key2': int}, total=False)]

    data = {'sub': [{'key1': 'hello'}]}
    result = howard.from_dict(data, TypedDictTest)
    assert isinstance(result, TypedDictTest)
    assert isinstance(result.sub, list)
    assert isinstance(result.sub[0], dict)

    test_dict = howard.to_dict(result)
    assert isinstance(test_dict, dict)
    assert isinstance(test_dict['sub'], list)


def test_with_advanced_typed_dict():
    @dataclass
    class TypedDictTest:
        pair: List[TypedDict('pair', {'drink': Drink, 'card': Card})]

    data = {'pair': [{'drink': {'name': 'milk'}, 'card': {'rank': 5, 'suit': 'h'}},
                     {'drink': {'name': 'gin'}, 'card': {'rank': 12, 'suit': 's'}}]}

    result = howard.from_dict(data, TypedDictTest)
    assert isinstance(result, TypedDictTest)
    assert isinstance(result.pair, list)
    assert isinstance(result.pair[0], dict)
    assert isinstance(result.pair[0]['drink'], Drink)
    assert isinstance(result.pair[0]['card'], Card)

    test_dict = howard.to_dict(result)
    assert isinstance(test_dict, dict)


def test_with_literals():
    @dataclass
    class LiteralCard:
        rank: int
        suit: Literal['heart', 'spade', 'diamond', 'club']

    with pytest.raises(TypeError):
        # suit isn't valid
        howard.from_dict({'rank': 13, 'suit': 'other'}, LiteralCard)

    result = howard.from_dict({'rank': 13, 'suit': 'spade'}, LiteralCard)
    assert isinstance(result, LiteralCard)

    final = howard.to_dict(result)
    assert isinstance(final, dict)
    assert isinstance(final['suit'], str)
