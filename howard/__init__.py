import abc
import dataclasses
from functools import singledispatch
from typing import TypeVar, Type, List, Tuple, Dict, Union
from collections.abc import Mapping
from enum import Enum, EnumMeta
from typing_extensions import Protocol, runtime


T = TypeVar("T", bound=Type)


def deserialize(d, t: T, *, cast: Type = None) -> T:
    if cast is dataclasses.dataclass:
        cast = DataClass

    return _convert_to(d, t, cast=cast)


def serialize(obj: object, *, as_type: Type = None):
    _type = as_type or type(obj)

    if _type is dataclasses.dataclass:
        _type = DataClass

    return _convert_from.dispatch(_type)(obj)


def _is_generic_type(t: Type) -> bool:
    """
    Returns whether a given type is a generic type
    """
    return (
        hasattr(t, "__parameters__")
        and hasattr(t, "__origin__")
        and hasattr(t, "__args__")
    )


def _get_runtime_type(obj, t: Type) -> Type:
    """
    Returns the matching runtime type for an object.
    If obj doesn't match the given t excepts with a TypeError.
    """
    if _is_generic_type(t):
        origin = t.__origin__

        if origin is Union or isinstance(obj, origin):
            return origin
        else:
            raise TypeError(f'Object "{obj}" not of expected type {t}')

    if isinstance(obj, t) or isinstance(t, EnumMeta):
        return t
    else:
        raise TypeError(f'Object "{obj}" not of expected type {t}')


@runtime
class Deserializable(Protocol):
    @classmethod
    def __deserialize__(cls, o):
        pass


def _convert_to(obj, t, *, cast=None):
    if cast:
        if not issubclass(t, cast):
            raise ValueError(
                f"Cannot cast {t} to {cast} because {t} is not a subclass of {cast}"
            )

    kwargs = {}

    if cast is None and hasattr(t, "__deserialize__") or cast is Deserializable:
        return t.__deserialize__(obj)

    elif cast is None and dataclasses.is_dataclass(t) or cast is DataClass:
        if not isinstance(obj, Mapping):
            raise TypeError(f"Serialized value for dataclass {t} must be a Mapping")

        fields = dataclasses.fields(t)

        for f in fields:
            if f.name in obj:
                # get value
                value = obj[f.name]
                kwargs[f.name] = _convert_to(value, f.type)
            elif (
                f.default_factory == dataclasses._MISSING_TYPE
                and f.default == dataclasses._MISSING_TYPE
                and f.init is True
            ):
                raise TypeError(
                    f"Mapping {obj} is missing field {f.name} required by dataclass {t}"
                )

        if len(obj) != len(kwargs):
            for key in obj:
                if key not in kwargs:
                    raise TypeError(
                        f"Key {key} appears in mapping {obj} but is not required by dataclass {t}"
                    )

        return t(**kwargs)

    # unwrap NewType
    if hasattr(t, "__supertype__"):
        t = t.__supertype__

    runtime_type = _get_runtime_type(obj, t)

    if runtime_type in {list, List} and _is_generic_type(t):
        item_type, = t.__args__
        return [_convert_to(item, item_type) for item in obj]

    elif runtime_type in {tuple, Tuple} and _is_generic_type(t):
        item_types = t.__args__

        if len(item_types) == 2 and item_types[1] == Ellipsis:
            item_type, _ = item_types
            return tuple(_convert_to(item, item_type) for item in obj)

        return tuple(
            _convert_to(item, item_type) for item, item_type in zip(obj, item_types)
        )

    elif runtime_type in {list, tuple}:
        return obj

    elif runtime_type in {dict, Dict}:
        key_type, value_type = t.__args__
        return {
            _convert_to(key, key_type): _convert_to(value, value_type)
            for key, value in obj.items()
        }

    elif runtime_type is Union:
        args = t.__args__
        for arg in args:
            try:
                return _convert_to(obj, arg)
            except TypeError:
                continue
        raise TypeError(f"{obj} didn't match any of the types of {t}")

    elif isinstance(runtime_type, EnumMeta):
        return t(obj)

    elif runtime_type in (int, float, str, bool):
        return obj

    else:
        raise TypeError(
            f"Type {t} currently not supported by howard. " "Consider making a PR."
        )


class DataClass(abc.ABC):
    """
    A class version for dataclasses.is_dataclass
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return dataclasses.is_dataclass(subclass)


@runtime
class Serializable(Protocol):
    def __serialize__(self):
        pass


class SerializableDataClass(DataClass, Serializable):
    def __serialize__(self):
        pass


@singledispatch
def _convert_from(obj):
    raise TypeError(f"Unsupported type {type(obj)}")


@_convert_from.register(Serializable)
@_convert_from.register(SerializableDataClass)
def _convert_from_custom_dict(obj):
    return obj.__serialize__()


@_convert_from.register(DataClass)
def _convert_from_dataclass(obj):
    return {
        f.name: _convert_from(getattr(obj, f.name)) for f in dataclasses.fields(obj)
    }


@_convert_from.register(list)
def _convert_from_list(obj):
    return [_convert_from(i) for i in obj]


@_convert_from.register(tuple)
def _convert_from_tuple(obj):
    return tuple(_convert_from(i) for i in obj)


@_convert_from.register(dict)
def _convert_from_dict(obj):
    return {k: _convert_from(v) for k, v in obj.items()}


@_convert_from.register(Enum)
def _convert_from_enum(obj):
    return _convert_from(obj.value)


@_convert_from.register(int)
@_convert_from.register(float)
@_convert_from.register(str)
@_convert_from.register(bool)
def _convert_from_primitive(obj):
    return obj
