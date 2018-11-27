# howard
Python datatype marshalling


This libary marshalls serialized objects (think JSON) into instances of defined containers and dataclasses and back.


i.e.

```python
from dataclasses import dataclass

import howard

@dataclass
class Person:
    name: str
    age: int


my_dict = {'name': 'Bob', 'age': 24}
person = howard.deserialize(my_dict, Person)
assert person.name == 'Bob'
assert person.age == 24
assert howard.serialize(person) == my_dict
```


to install:

```bash
pip install howard
```
