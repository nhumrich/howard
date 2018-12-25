import dataclasses
from typing_extensions import Protocol, runtime
from collections.abc import Mapping
from typing import Union, Dict, List, Tuple, TypeVar, Type
from enum import EnumMeta
from .type_util import get_runtime_type, is_generic_type, DataClass


@runtime
class Deserializable(Protocol):
    @classmethod
    def __deserialize__(cls, o):
        pass


def _convert_to(obj, t, *, cast=None):
    # unwrap NewType
    if hasattr(t, "__supertype__"):
        t = t.__supertype__

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

    runtime_type = get_runtime_type(obj, t)

    if runtime_type in {list, List} and is_generic_type(t):
        item_type, = t.__args__
        return [_convert_to(item, item_type) for item in obj]

    elif runtime_type in {tuple, Tuple} and is_generic_type(t):
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
        errors: Dict[Type, TypeError] = {}
        for arg in args:
            try:
                return _convert_to(obj, arg)
            except TypeError as error:
                errors[arg] = error

        raise TypeError(
            f"{obj} didn't match any of the types of {t}.\n"
            + "\n".join(
                f"TypeError({error}) was raised for type {_type}"
                for _type, error in errors.items()
            )
        )

    elif isinstance(runtime_type, EnumMeta):
        return t(obj)

    elif runtime_type in (int, float, str, bool):
        if not isinstance(obj, runtime_type):
            raise TypeError(f"{obj} didn't match {runtime_type}")

        return obj

    else:
        raise TypeError(
            f"Type {t} currently not supported by howard. " "Consider making a PR."
        )


T = TypeVar("T", bound=Type)


class Deserializer:
    def deserialize(self, d, t: T, *, cast: Type = None) -> T:
        if cast is dataclasses.dataclass:
            cast = DataClass

        return _convert_to(d, t, cast=cast)
