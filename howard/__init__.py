import dataclasses
from typing import Generic, TypeVar
from enum import EnumMeta


T = TypeVar('T')


def from_dict(d: dict, t: Generic[T], decoders=None) -> T:
    """
    Initialise an instance of the dataclass t using the values in the dict d

    Example:

    >>> @dataclasses.dataclass
    ... class Person:
    ...     name: str
    ...     age: int
    ...
    >>> data = {'name': 'Howard', 'age': 24}
    >>> from_dict(data, Person)
    Person(name='Howard', age=24)
    """
    if not isinstance(d, dict):
        raise TypeError("First argument must be of type dict")
    if not dataclasses.is_dataclass(t):
        raise TypeError("Second argument must be a dataclass")

    return _convert_to(d, t, decoders if decoders else {})


def to_dict(obj: T, public_only=False, encoders=None) -> dict:
    """
    Marshall a dataclass instance into a dict

    Example:

    >>> @dataclasses.dataclass
    ... class Person:
    ...     name: str
    ...     age: int
    ...
    >>> instance = Person(name='Howard', age=24)
    >>> to_dict(instance)
    {'name': 'Howard', 'age': 24}
    """
    if not dataclasses.is_dataclass(obj):
        raise TypeError('Argument must be a dataclass')

    return _convert_from(obj, public=public_only, encoders=encoders if encoders else {})


def _convert_to(obj, t, decoders):
    kwargs = {}
    if dataclasses.is_dataclass(t):
        for f in dataclasses.fields(t):
            if f.name in obj:
                # get value
                value = obj[f.name]
                kwargs[f.name] = _convert_to(value, f.type, decoders)
        return t(**kwargs)

    elif hasattr(t, '__origin__'):  # i.e List from typing
        args = t.__args__
        real_type = t.__origin__

        # validate
        if not isinstance(obj, real_type):
            raise TypeError(f'Object "{obj}" not of expected type {real_type}')

        if real_type == list:
            return [_convert_to(i, args[0], decoders) for i in obj]
        elif real_type == dict:
            return {_convert_to(k, args[0], decoders): _convert_to(v, args[1], decoders) for k, v in obj.items()}
        else:
            raise TypeError('Type {real_type} currently not supported by howard. '
                            'Consider making a PR.')
    elif isinstance(t, EnumMeta):
        return t(obj)

    elif t in decoders:
        return decoders[t](obj)

    elif t in (int, str, bool):
        if not isinstance(obj, t):
            raise TypeError(f'Object "{obj}" not of expected type {t}')
        return obj
    else:
        raise TypeError(f'Unsupported type {t}')


def _convert_from(obj, public=False, encoders=None):
    encoders = encoders if encoders else {}
    if dataclasses.is_dataclass(obj):
        d = {}
        for f in dataclasses.fields(obj):
            if f.name.startswith('_') and public:
                continue  # these attributes dont make it into the dict
            if f.metadata.get('internal', False):
                continue  # these attributes are marked as internal
            d[f.name] = _convert_from(getattr(obj, f.name), public=public, encoders=encoders)
        return d
    elif isinstance(obj, list):
        return [_convert_from(i, public=public, encoders=encoders) for i in obj]
    elif isinstance(obj, dict):
        return {k: _convert_from(v, public=public, encoders=encoders) for k, v in obj.items()}
    elif isinstance(obj.__class__, EnumMeta):
        return _convert_from(obj.value, public=public, encoders=encoders)
    elif type(obj) in encoders:
        return encoders[type(obj)](obj)
    elif type(obj) in (int, str, bool):
        return obj
    else:
        raise TypeError(f'Unsupported type {type(obj)}')
