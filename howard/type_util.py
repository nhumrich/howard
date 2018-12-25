import abc
import dataclasses
from typing import Type


def is_generic_type(t: Type) -> bool:
    """
    Returns whether a given type is a generic type
    """
    return (
        hasattr(t, "__parameters__")
        and hasattr(t, "__origin__")
        and hasattr(t, "__args__")
    )


def get_runtime_type(obj, t: Type) -> Type:
    """
    Returns the matching runtime type for an object.
    If obj doesn't match the given t excepts with a TypeError.
    """
    if is_generic_type(t):
        origin = t.__origin__
        return origin

    return t


class DataClass(abc.ABC):
    """
    A class version for dataclasses.is_dataclass
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return dataclasses.is_dataclass(subclass)
