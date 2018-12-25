from .serializer import Serializer
from .deserializer import Deserializer

default_serializer = Serializer()
serialize = default_serializer.serialize

default_deserializer = Deserializer()
deserialize = default_deserializer.deserialize
