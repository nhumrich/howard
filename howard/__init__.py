import dataclasses
from functools import singledispatch
from typing import TypeVar, Type, List, Dict, Union
from enum import Enum, EnumMeta
from typing_extensions import Protocol, runtime


T = TypeVar("T", bound=Type)


def deserialize(d, t: T) -> T:
    return _convert_to(d, t)


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
    # NewType
    if hasattr(t, "__supertype__"):
        return _get_runtime_type(obj, t.__supertype__)

    if _is_generic_type(t):
        args = t.__args__
        origin = t.__origin__

        if origin is Union:
            for arg in args:
                try:
                    runtime_type = _get_runtime_type(obj, arg)
                    return runtime_type
                except TypeError:
                    continue
            raise TypeError(f"{obj} didn't match any of the types of {t}")
        else:
            if isinstance(obj, origin):
                return origin
            else:
                raise TypeError(f'Object "{obj}" not of expected type {t}')

    if isinstance(obj, t) or isinstance(t, EnumMeta):
        return t
    else:
        raise TypeError(f'Object "{obj}" not of expected type {t}')


def _convert_to(obj, t):
    kwargs = {}

    if hasattr(t, "__deserialize__"):
        return t.__deserialize__(obj)

    elif dataclasses.is_dataclass(t):
        for f in dataclasses.fields(t):
            if f.name in obj:
                # get value
                value = obj[f.name]
                kwargs[f.name] = _convert_to(value, f.type)
        return t(**kwargs)

    runtime_type = _get_runtime_type(obj, t)

    if runtime_type in {list, List}:
        item_type, = t.__args__
        return [_convert_to(item, item_type) for item in obj]

    elif runtime_type in {dict, Dict}:
        key_type, value_type = t.__args__
        return {
            _convert_to(key, key_type): _convert_to(value, value_type)
            for key, value in obj.items()
        }

    elif isinstance(runtime_type, EnumMeta):
        return t(obj)

    elif runtime_type in (int, str, bool):
        return obj

    else:
        raise TypeError(
            f"Type {t} currently not supported by howard. " "Consider making a PR."
        )


@runtime
class DataClass(Protocol):
    """
    A protocol version for dataclasses.is_dataclass
    """

    # "__dataclass_fields__" == dataclasses._FIELDS
    __dataclass_fields__: Dict[str, dataclasses.Field]


@runtime
class Serializable(Protocol):
    def __serialize__(self):
        pass


@runtime
class SerializableDataClass(Serializable, DataClass, Protocol):
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
