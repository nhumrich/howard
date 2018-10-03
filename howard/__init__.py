import dataclasses
from typing import Generic, TypeVar
from enum import EnumMeta


T = TypeVar('T')


def from_dict(d: dict, t: Generic[T]) -> T:
    if not isinstance(d, dict):
        raise TypeError("First argument must be of type dict")
    if not dataclasses.is_dataclass(t):
        raise TypeError("Second argument must be a dataclass")

    return _convert_to(d, t)


def to_dict(obj: T) -> dict:
    if not dataclasses.is_dataclass(obj):
        raise TypeError('Argument must be a dataclass')

    return _convert_from(obj)


def _convert_to(obj, t):
    kwargs = {}
    if dataclasses.is_dataclass(t):
        for f in dataclasses.fields(t):
            if f.name in obj:
                # get value
                value = obj[f.name]
                kwargs[f.name] = _convert_to(value, f.type)
        return t(**kwargs)

    elif hasattr(t, '__origin__'):  # i.e List from typing
        args = t.__args__
        real_type = t.__origin__

        # validate
        if not isinstance(obj, real_type):
            raise TypeError(f'Object "{obj}" not of expected type {real_type}')

        if real_type == list:
            return [_convert_to(i, args[0]) for i in obj]
        elif real_type == dict:
            return {k: _convert_from(v) for k, v in obj.items()}
        else:
            raise TypeError('Type {real_type} currently not supported by howard. '
                            'Consider making a PR.')
    elif isinstance(t, EnumMeta):
        return t(obj)

    elif t in (int, str, bool):
        if not isinstance(obj, t):
            raise TypeError(f'Object "{obj}" not of expected type {t}')
        return obj
    else:
        raise TypeError(f'Unsupported type {t}')


def _convert_from(obj):
    if dataclasses.is_dataclass(obj):
        d = {}
        for f in dataclasses.fields(obj):
            d[f.name] = _convert_from(getattr(obj, f.name))
        return d
    elif isinstance(obj, list):
        return [_convert_from(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _convert_from(v) for k, v in obj.items()}
    elif isinstance(obj.__class__, EnumMeta):
        return _convert_from(obj.value)
    elif type(obj) in (int, str, bool):
        return obj
    else:
        raise TypeError(f'Unsupported type {type(obj)}')
