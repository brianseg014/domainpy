import pytest
from unittest import mock

from domainpy.exceptions import MapperNotFoundError
from domainpy.infrastructure.mappers import MapperSet


def test_is_deserialize():
    mapper1 = mock.MagicMock()
    mapper2 = mock.MagicMock()
    mapper2.is_deserializable = mock.Mock(return_value=True)

    deserializable = {}
    mapper_set = MapperSet([mapper1, mapper2])
    assert mapper_set.is_deserializable(deserializable)

def test_deserialize():
    deserialized = {}

    mapper1 = mock.MagicMock()
    mapper1.is_deserializable = mock.Mock(return_value=False)
    mapper2 = mock.MagicMock()
    mapper2.is_deserializable = mock.Mock(return_value=True)

    deserializable = {}
    mapper_set = MapperSet([mapper1, mapper2])
    mapper_set.deserialize(deserializable)

    mapper1.deserialize.assert_not_called()
    mapper2.deserialize.assert_called()

def test_deserialize_no_mapper_found():
    mapper_set = MapperSet([])

    deserializable = {}

    with pytest.raises(MapperNotFoundError):
        mapper_set.deserialize(deserializable)