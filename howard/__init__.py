import dataclasses
from datetime import datetime
import dateutil.parser
import typing
from typing import TypeVar, Union, Type
from enum import EnumMeta


T = TypeVar('T')


class HowardError(TypeError):
    """ Used when howard cant correctly parse because the types dont match """


def from_dict(d: dict, t: Type[T], ignore_extras: bool = True) -> T:
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
        raise HowardError("First argument must be of type dict")
    if not dataclasses.is_dataclass(t):
        raise HowardError("Second argument must be a dataclass")

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
        raise HowardError('Argument must be a dataclass')

    return _convert_from(obj, public=public_only)


def _convert_to(obj, t, ignore_extras=True):
    kwargs = {}
    if t == typing.Any:
        return obj
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
                raise HowardError(
                    f'Found unexpected keys {extras} when converting to {t}'
                )
        return t(**kwargs)

    elif t == dict:
        return _convert_to(obj, typing.Dict[typing.Any, typing.Any], ignore_extras=ignore_extras)
    elif t == list:
        return _convert_to(obj, typing.List[typing.Any], ignore_extras=ignore_extras)
    elif typing.get_origin(t):  # A typing "mask" type, i.e List/Dict
        args = typing.get_args(t)
        real_type = typing.get_origin(t)

        if real_type == Union:
            if type(None) in args and obj is None:
                # an `Optional[x]` type or `Union[x, y, None]` type
                if obj is None:
                    return obj
            for arg in args:
                try:
                    return _convert_to(obj, arg, ignore_extras=ignore_extras)
                except HowardError:
                    continue
            raise HowardError(f'{obj} could not be converted to any type in: '
                            f'{", ".join(f"{a}" for a in args)}')

        if real_type == typing.Literal:
            if obj not in args:
                raise HowardError(f'Invalid value "{obj}". Must be one of: {", ".join(args)}')
            return obj

        # validate
        if not isinstance(obj, real_type):
            raise HowardError(f'Object "{obj}" not of expected type {real_type}')

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
            raise HowardError(
                'Type {real_type} currently not supported by howard. '
                'Consider making a PR.'
            )
    elif isinstance(t, typing._TypedDictMeta):
        # is a TypedDict
        result = {}
        for key, value in typing.get_type_hints(t).items():
            if key not in obj:
                if t.__total__:
                    raise HowardError(f'Object "{obj}" is missing required key: {key}')
            else:
                result[key] = _convert_to(obj[key], value, ignore_extras=ignore_extras)
        hints = typing.get_type_hints(t)
        if not ignore_extras:
            for key in obj:
                if key not in hints:
                    raise HowardError(f'Found unexpected key {key} when converting to {t}')
        return result

    elif isinstance(t, EnumMeta):
        return t(obj)
    elif hasattr(t, '__supertype__'):
        # is a Vanity type, such as `A = NewType('A', str)`
        return _convert_to(obj, t.__supertype__, ignore_extras=ignore_extras)
    elif t in (int, str, bool, float):
        if not isinstance(obj, t):
            raise HowardError(f'Object "{obj}" not of expected type {t}')
        return t(obj)
    elif t is datetime:
        return dateutil.parser.parse(obj)
    else:
        raise HowardError(f'Unsupported type {t}')


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
        raise HowardError(f'Unsupported type {type(obj)}')
