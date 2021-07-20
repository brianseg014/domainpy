import decimal

from boto3.dynamodb.types import (  # type: ignore
    TypeDeserializer,
    TypeSerializer,
)

type_serializer = TypeSerializer()
type_deserializer = TypeDeserializer()


def serialize(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = serialize(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = serialize(obj[k])
        return obj
    elif isinstance(obj, float):
        return decimal.Decimal(str(obj))
    else:
        return obj


def deserialize(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = deserialize(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = deserialize(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def client_serialize(obj):
    return type_serializer.serialize(serialize(obj))


def client_deserialize(obj):
    return type_deserializer.deserialize(deserialize(obj))
