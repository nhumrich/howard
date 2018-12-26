import abc
import dataclasses
from typing_extensions import Protocol, runtime
from functools import singledispatch, partial
from collections.abc import Mapping
from typing import Union, Dict, List, Tuple, TypeVar, Type
from enum import Enum
from .type_util import get_runtime_type, is_generic_type, unwrap_new_type, DataClass


@runtime
class Deserializable(Protocol):
    @classmethod
    def __deserialize__(cls, o):
        pass


def _convert_to_new_type(obj, t, *, deserializer):
    return deserializer.deserialize(obj, t.__supertype__)


def _convert_to_deserializable(obj, t, *, deserializer):
    return t.__deserialize__(obj)


def _convert_to_dataclass(obj, t, *, deserializer):
    if not isinstance(obj, Mapping):
        raise TypeError(f"Serialized value for dataclass {t} must be a Mapping")

    kwargs = {}

    for f in dataclasses.fields(t):
        if f.name in obj:
            # get value
            value = obj[f.name]
            kwargs[f.name] = deserializer.deserialize(value, f.type)
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


def _convert_to_generic_list(obj, t, *, deserializer):
    item_type, = t.__args__
    return [deserializer.deserialize(item, item_type) for item in obj]


def _convert_to_generic_tuple(obj, t, *, deserializer):
    item_types = t.__args__

    if len(item_types) == 2 and item_types[1] == Ellipsis:
        item_type, _ = item_types
        return tuple(deserializer.deserialize(item, item_type) for item in obj)

    return tuple(
        deserializer.deserialize(item, item_type)
        for item, item_type in zip(obj, item_types)
    )


def _convert_to_generic_dict(obj, t, *, deserializer):
    key_type, value_type = t.__args__
    return {
        deserializer.deserialize(key, key_type): deserializer.deserialize(
            value, value_type
        )
        for key, value in obj.items()
    }


def _convert_to_simple_type(obj, t, *, deserializer):
    if not isinstance(obj, t):
        raise TypeError(f"{obj} didn't match {t}")

    return obj


def _convert_to_union(obj, t, *, deserializer):
    args = t.__args__
    errors: Dict[Type, TypeError] = {}
    for arg in args:
        try:
            return deserializer.deserialize(obj, arg)
        except TypeError as error:
            errors[arg] = error

    raise TypeError(
        f"{obj} didn't match any of the types of {t}.\n"
        + "\n".join(
            f"TypeError({error}) was raised for type {_type}"
            for _type, error in errors.items()
        )
    )


def _convert_to_enum_meta(obj, t, *, deserializer):
    return t(obj)


def _convert_to(obj, t, *, deserializer):
    if not isinstance(obj, t):
        raise TypeError(
            f"{obj} didn't match {t}. To define a custom behavior for the type either implement a __deserialize__() class method for {t} or register a method for {t} in the {deserializer}"
        )

    return obj


T = TypeVar("T", bound=Type)


class Deserializer:
    def __init__(self):
        self._convert_to = singledispatch(_convert_to)
        self._convert_to.register(Deserializable)(_convert_to_deserializable)
        self._convert_to.register(DataClass)(_convert_to_dataclass)
        self._convert_to.register(Enum)(_convert_to_enum_meta)

    def deserialize(self, d, t: T) -> T:
        t = unwrap_new_type(t)

        return self.dispatch(t)(d, t)

    def dispatch(self, _type):
        _type = unwrap_new_type(_type)

        # Handle Generic Aliases
        if is_generic_type(_type):
            runtime_type = get_runtime_type(_type)

            if runtime_type in {list, List}:
                return partial(_convert_to_generic_list, deserializer=self)

            elif runtime_type in {tuple, Tuple}:
                return partial(_convert_to_generic_tuple, deserializer=self)

            elif runtime_type in {dict, Dict}:
                return partial(_convert_to_generic_dict, deserializer=self)

            elif runtime_type is Union:
                return partial(_convert_to_union, deserializer=self)

        if _type is dataclasses.dataclass:
            _type = DataClass

        return partial(self._convert_to.dispatch(_type), deserializer=self)

    def register(self, _type):
        return self._convert_to.register(_type)
