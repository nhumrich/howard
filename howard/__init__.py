import dataclasses
from functools import singledispatch
from typing import Generic, TypeVar, Type, List, Dict
from enum import Enum, EnumMeta
from typing_extensions import Protocol, runtime


T = TypeVar("T", bound=Type)


def from_dict(d: dict, t: T) -> T:
    if not isinstance(d, dict):
        raise TypeError("First argument must be of type dict")
    if not dataclasses.is_dataclass(t):
        raise TypeError("Second argument must be a dataclass")

    return _convert_to(d, t)


def to_dict(obj: object, *, as_type: Type = None) -> dict:
    _type = as_type or type(obj)

    if not dataclasses.is_dataclass(_type) and _type is not dataclasses.dataclass:
        raise TypeError("Argument must be a dataclass")

    if _type is dataclasses.dataclass:
        _type = DataClass

    return _convert_from.dispatch(_type)(obj)


def _convert_to(obj, t):
    kwargs = {}

    if hasattr(t, "from_dict"):
        return t.from_dict(obj)

    elif dataclasses.is_dataclass(t):
        for f in dataclasses.fields(t):
            if f.name in obj:
                # get value
                value = obj[f.name]
                kwargs[f.name] = _convert_to(value, f.type)
        return t(**kwargs)

    elif hasattr(t, "__origin__"):  # i.e List from typing
        args = t.__args__
        real_type = t.__origin__

        # validate
        if not isinstance(obj, real_type):
            raise TypeError(f'Object "{obj}" not of expected type {real_type}')

        if real_type in {list, List}:
            return [_convert_to(i, args[0]) for i in obj]
        elif real_type in {dict, Dict}:
            return {
                _convert_to(k, args[0]): _convert_to(v, args[1]) for k, v in obj.items()
            }
        else:
            raise TypeError(
                f"Type {real_type} currently not supported by howard. "
                "Consider making a PR."
            )
    elif isinstance(t, EnumMeta):
        return t(obj)

    elif t in (int, str, bool):
        if not isinstance(obj, t):
            raise TypeError(f'Object "{obj}" not of expected type {t}')
        return obj
    else:
        raise TypeError(f"Unsupported type {t}")


@runtime
class DataClass(Protocol):
    """
    A protocol version for dataclasses.is_dataclass
    """

    # "__dataclass_fields__" == dataclasses._FIELDS
    __dataclass_fields__: Dict[str, dataclasses.Field]


@runtime
class CustomToDict(DataClass, Protocol):
    def to_dict(self):
        pass


@singledispatch
def _convert_from(obj):
    raise TypeError(f"Unsupported type {type(obj)}")


@_convert_from.register(CustomToDict)
def _convert_from_custom_dict(obj):
    return obj.to_dict()


@_convert_from.register(DataClass)
def _convert_from_dataclass(obj):
    return {
        f.name: _convert_from(getattr(obj, f.name)) for f in dataclasses.fields(obj)
    }


@_convert_from.register(list)
def _convert_from_list(obj):
    return [_convert_from(i) for i in obj]


@_convert_from.register(dict)
def _convert_from_dict(obj):
    return {k: _convert_from(v) for k, v in obj.items()}


@_convert_from.register(Enum)
def _convert_from_enum(obj):
    return _convert_from(obj.value)


@_convert_from.register(int)
@_convert_from.register(str)
@_convert_from.register(bool)
def _convert_from_primitive(obj):
    return obj
