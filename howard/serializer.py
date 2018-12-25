import abc
import dataclasses
from functools import singledispatch
from copy import copy
from enum import Enum
from typing import Optional, Type, Callable, Any
from typing_extensions import Protocol, runtime
from .type_util import DataClass


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


class Serializer:
    def __init__(self):
        self._convert_from = copy(_convert_from)

    def serialize(self, obj: object, *, as_type: Optional[Type] = None):
        _type = as_type or type(obj)

        if _type is dataclasses.dataclass:
            _type = DataClass

        return self._convert_from.dispatch(_type)(obj)

    def register(self, type_serializer: Callable):
        self._convert_from.register(type_serializer)
