# howard
Python datatype marshalling


This library marshalls dictionaries [read json] into instances of defined dataclasses and back.

i.e.

```python
from dataclasses import dataclass

import howard

@dataclass
class Person:
    name: str
    age: int


my_dict = {'name': 'Bob', 'age': 24}
person = howard.from_dict(my_dict, Person)
assert person.name == 'Bob'
assert person.age == 24
```

The main purpose is to use python dataclasses as a schema definition rather than having to hand-write a schema. 
Howard does not currently include logic itself for generating json-schema (swagger) object documentation, but that is a long term goal of it.
 
Howard differs from a standard dataclass because it can recursively marshall and unmarshall. 
It also supports more types out of the box than `dataclasses.asdict` does. Some supported types:

* Enums
* TypedDict
* Collections (lists/dictionaries)
* Datetime
* all primitives (int/string/boolean/float)

All of the logic for howard is in your dataclass definition, not in howard. Howard just has a `to_dict` and `from_dict` method,
and it bases all decisions off of your dataclass. There is no inheritance on custom types, everything is standard, built-in python. (3.7+)
   

## Installing

```bash
pip install howard
```

## More examples

For more examples, you can go look at the tests at [tests/test_howard.py](tests/test_howard.py)

Here is a basic example of recursive types and how it can work with howard:

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List

import howard

@dataclass
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
    rank: int = field(metadata={'howard': {'decoder': validate_rank}})
    suit: Suit


@dataclass
class Hand:
    hand_id: int = 0
    cards: List[Card] = field(default_factory=list)


d = {'hand_id': 2, 'cards': [{'rank': 2, 'suit': 'c'}, {'rank': 10, 'suit': 'h'}]}

# d is a dictionary, now we turn it into the dataclass
obj = howard.from_dict(d, Hand)

assert isinstance(obj, Hand)
assert obj.hand_id == 2
assert len(obj.cards) == 2
assert isinstance(obj.cards[0], Card)
assert obj.cards[0].suit == Suit.club

# and back to a dictionary
json_dict = howard.to_dict(obj)
```

In the above example, you can see a couple things. 
1. A `Hand` contains a list of `Card`.
2. The sub-object `Card` also gets unmarshalled correctly.
3. The `Suit` object is an enum, which is like a string in json form, but only has 4 possible values.
4. The `Card` has a field called `rank` which has its own custom decoder. 
    In this case, the decoder acts as a validator, but can also be used for custom decode logic. 



# FAQ
* **Why not just use `dataclasses.asdict` and `MyDataclass(**my_dict)`?** 
  `dataclasses.asdict` doesn't work on all types, for example, Enums or datetimes.
  `MyDataclass(**my_dict)` will not recursively turn the subobjects into their respective datatype.

* **What about custom types?**
  You can specify custom decoders and encoders in a dataclass `field.metadata` section. See example above.