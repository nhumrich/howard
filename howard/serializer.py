import abc
import dataclasses
from functools import singledispatch, partial
from enum import Enum
from typing import Type, Callable, Union
from typing_extensions import Protocol, runtime
from .type_util import DataClass


@runtime
class Serializable(Protocol):
    def __serialize__(self):
        pass


class SerializableDataClass(DataClass, Serializable):
    def __serialize__(self):
        pass


def _convert_from(obj, *, serializer):
    return obj


def _convert_from_serializable(obj, *, serializer):
    return obj.__serialize__()


def _convert_from_dataclass(obj, *, serializer):
    return {
        f.name: serializer.serialize(getattr(obj, f.name))
        for f in dataclasses.fields(obj)
    }


def _convert_from_list(obj, *, serializer):
    return [serializer.serialize(i) for i in obj]


def _convert_from_tuple(obj, *, serializer):
    return tuple(serializer.serialize(i) for i in obj)


def _convert_from_dict(obj, *, serializer):
    return {k: serializer.serialize(v) for k, v in obj.items()}


def _convert_from_enum(obj, *, serializer):
    return serializer.serialize(obj.value)


class Serializer:
    def __init__(self):
        self._convert_from = singledispatch(_convert_from)
        self._convert_from.register(Serializable)(_convert_from_serializable)
        self._convert_from.register(SerializableDataClass)(_convert_from_dataclass)
        self._convert_from.register(DataClass)(_convert_from_dataclass)
        self._convert_from.register(list)(_convert_from_list)
        self._convert_from.register(tuple)(_convert_from_tuple)
        self._convert_from.register(dict)(_convert_from_dict)
        self._convert_from.register(Enum)(_convert_from_enum)

    def serialize(self, obj: object):
        return self.dispatch(type(obj))(obj)

    def dispatch(self, _type: Union[object, Type]) -> Callable:
        if _type is dataclasses.dataclass:
            _type = DataClass

        return partial(self._convert_from.dispatch(_type), serializer=self)

    def register(self, _type: Type):
        return self._convert_from.register(_type)
