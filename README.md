# howard

Python datatype marshalling

This libary marshalls serialized objects (think JSON) into instances of defined classes and back.

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

### Development

Requires: pyenv & pipenv

```bash
# Install Python 3.7
pyenv install 3.7;
# Create a Python 3.7 venv
PIPENV_VENV_IN_PROJECT=1 pipenv install --python $(pyenv root)/versions/3.7.0/bin/python;
# Install dependencies
pipenv install --dev;
```
