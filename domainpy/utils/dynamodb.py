import decimal

from boto3.dynamodb.types import (  # type: ignore
    TypeDeserializer,
    TypeSerializer,
)

type_serializer = TypeSerializer()
type_deserializer = TypeDeserializer()


def serialize(obj):
    if isinstance(obj, list):
        return [serialize(i) for i in obj]

    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}

    if isinstance(obj, float):
        return decimal.Decimal(str(obj))

    return obj


def deserialize(obj):
    if isinstance(obj, list):
        return [deserialize(i) for i in obj]

    if isinstance(obj, dict):
        return {k: deserialize(v) for k, v in obj.items()}

    if isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)

    return obj


def client_serialize(obj):
    return type_serializer.serialize(serialize(obj))


def client_deserialize(obj):
    return type_deserializer.deserialize(deserialize(obj))
