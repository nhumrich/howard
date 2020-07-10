import dataclasses
from datetime import datetime
import dateutil.parser
import typing
from typing import TypeVar, Union, TypedDict
from enum import EnumMeta


T = TypeVar('T')


def from_dict(d: dict, t: T, ignore_extras: bool = True) -> T:
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

    return _convert_to(d, t, ignore_extras)


def to_dict(obj: T, public_only=False) -> dict:
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

    return _convert_from(obj, public=public_only)


def _convert_to(obj, t, ignore_extras=True):
    kwargs = {}
    if dataclasses.is_dataclass(t):
        for f in dataclasses.fields(t):
            if f.name in obj:
                # get value
                value = obj[f.name]
                decoder = f.metadata.get('howard', {}).get('decoder')
                if decoder:
                    kwargs[f.name] = decoder(value)
                else:
                    kwargs[f.name] = _convert_to(value, f.type, ignore_extras=ignore_extras)

        if not ignore_extras:
            extras = set(obj.keys()) - set(kwargs.keys())
            if extras:
                raise TypeError(
                    f'Found unexpected keys {extras} when converting to {t}'
                )
        return t(**kwargs)

    elif hasattr(t, '__origin__'):  # i.e List from typing
        args = t.__args__
        real_type = t.__origin__

        # Handle Union types by assuming Optional
        # TODO: support real Union types
        if real_type == Union and args[-1] == type(None):
            if obj is None:
                return obj
            else:
                return _convert_to(obj, args[0])

        # validate
        if not isinstance(obj, real_type):
            raise TypeError(f'Object "{obj}" not of expected type {real_type}')

        if real_type == list:
            return [
                _convert_to(i, args[0], ignore_extras=ignore_extras)
                for i in obj
            ]
        elif real_type == dict:
            return {
                _convert_to(k, args[0], ignore_extras=ignore_extras):
                    _convert_to(v, args[1], ignore_extras=ignore_extras)
                for k, v in obj.items()
            }
        else:
            raise TypeError(
                'Type {real_type} currently not supported by howard. '
                'Consider making a PR.'
            )
    elif isinstance(t, typing._TypedDictMeta):
        # is a TypedDict
        result = {}
        for key, value in t.__annotations__.items():
            if key not in obj:
                if t.__total__:
                    raise TypeError(f'Object "{obj}" is missing required key: {key}')
            else:
                result[key] = _convert_to(obj[key], value, ignore_extras=ignore_extras)
        if not ignore_extras:
            for key in obj:
                if key not in t.__annotations__:
                    raise TypeError(f'Found unexpected key {key} when converting to {t}')
        return result

    elif isinstance(t, EnumMeta):
        return t(obj)

    elif t in (int, str, bool, float):
        if not isinstance(obj, t):
            raise TypeError(f'Object "{obj}" not of expected type {t}')
        return obj
    elif t is datetime:
        return dateutil.parser.parse(obj)
    else:
        raise TypeError(f'Unsupported type {t}')


def _convert_from(obj, public=False):
    if dataclasses.is_dataclass(obj):
        d = {}
        for f in dataclasses.fields(obj):
            if f.name.startswith('_') and public:
                continue  # these attributes dont make it into the dict
            if f.metadata.get('internal', False):
                continue  # these attributes are marked as internal
            encoder = f.metadata.get('howard', {}).get('encoder')
            if encoder:
                d[f.name] = encoder(getattr(obj, f.name))
            else:
                d[f.name] = _convert_from(getattr(obj, f.name), public=public)
        return d
    elif isinstance(obj, list):
        return [_convert_from(i, public=public) for i in obj]
    elif isinstance(obj, dict):
        return {k: _convert_from(v, public=public) for k, v in obj.items()}
    elif isinstance(obj.__class__, EnumMeta):
        return _convert_from(obj.value, public=public)
    elif type(obj) in (int, str, bool, float):
        return obj
    elif obj is None:
        return obj
    elif type(obj) is datetime:
        return obj.isoformat()
    else:
        raise TypeError(f'Unsupported type {type(obj)}')
