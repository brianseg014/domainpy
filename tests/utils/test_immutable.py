import pytest

from domainpy.utils.immutable import Immutable


def test_immutable():
    immutable = Immutable()

    with pytest.raises(AttributeError):
        immutable.some_property = 'x'
    