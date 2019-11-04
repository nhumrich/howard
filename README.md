# howard
Python datatype marshalling


This libary marshalls dictionaries (think json) into instances of defined dataclasses and back.


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


to install:

```bash
pip install howard
```
