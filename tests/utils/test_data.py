import sys
import pytest
import typing

from domainpy.utils.data import SystemData


def test_constructor():
    Data = type(
        'Message', 
        (SystemData,), 
        {
            '__annotations__': {
                'some_property': str,
                'some_other_property': int,
                'some_optional_property': typing.Optional[str],
                'some_defaulted_property': str
            },
            'some_defaulted_property': 'x'
        }
    )

    x = Data(some_property='x', some_other_property=1, some_optional_property=None)
    
    assert x.some_property == 'x'
    assert x.some_other_property == 1
    assert x.some_optional_property == None
    assert x.some_defaulted_property == 'x'

    x = Data(some_property='x', some_other_property=1, some_optional_property='x')
    assert x.some_optional_property == 'x'

def test_inheritance():
    Data = type(
        'Data', 
        (SystemData,), 
        {
            '__annotations__': {
                'some_property': str,
                'some_other_property': int,
                'some_defaulted_property': str
            },
            'some_defaulted_property': 'x'
        }
    )
    SubData = type(
        'SubData',
        (Data,),
        {
            '__annotations__': {
                'some_new_property': str,
                'some_defaulted_property': str
            },
            'some_defaulted_property': 'y'
        }
    )
    x = SubData(
        some_property='x', 
        some_other_property=1, 
        some_new_property='x'
    )
    assert x.some_property == 'x'
    assert x.some_other_property == 1
    assert x.some_defaulted_property == 'y' # Override property default
    assert x.some_new_property == 'x'

def test_fail_on_mismatch_type():
    Data = type(
        'Data', 
        (SystemData,),
        {
            '__annotations__': {
                'some_property': str,
                'some_other_property': int
            }
        }
    )
    with pytest.raises(TypeError):
        x = Data(some_property=1, some_other_property='x')

def test_kwargs():
    x = SystemData(some_property='x')
    assert x.some_property == 'x'

def test_construct_with_custom_type():
    CustomData = type(
        'CustomData',
        (SystemData,),
        { }
    )
    ContainerData = type(
        'ContainerData',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': CustomData,
                'some_other_property': typing.Tuple[CustomData, ...]
            }
        }
    )
    x = ContainerData(
        some_property=CustomData(), 
        some_other_property=tuple([
            CustomData()
        ])
    )
    assert isinstance(x.some_property, CustomData)
    assert isinstance(x.some_other_property[0], CustomData)

def test_do_not_replace_existing_init():
    class Message(SystemData):
        some_property: str

        def __init__(self) -> None:
            pass

    with pytest.raises(TypeError):
        x = Message(some_property='y')

def test_from_dict():
    Data = type(
        'Data', 
        (SystemData,), 
        {
            '__annotations__': {
                'some_property': typing.Optional[str],
            }
        }
    )

    dct = {
        'some_property': 'x'
    }

    x = Data.__from_dict__(dct)
    assert x.some_property == 'x'

    dct = {
        'some_property': None
    }

    x = Data.__from_dict__(dct)
    assert x.some_property == None

def test_from_dict_nested():
    Data = type(
        'Data',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': str
            }
        }
    )
    ContainerData = type(
        'ContainerData',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': Data
            }
        }
    )
    dct = {
        'some_property': {
            'some_property': 'x'
        }
    }
    x = ContainerData.__from_dict__(dct)
    assert x.some_property.some_property == 'x'

@pytest.mark.skipif(sys.version_info < (3,9), reason="requires python3.9 or higher")
def test_from_dict_sequence():
    Data = type(
        'Data',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': str
            }
        }
    )
    ContainerData = type(
        'ContainerMessage',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': tuple[str, ...],
                'some_other_property': tuple[Data, ...]
            }
        }
    )

    dct = {
        'some_property': ['x', 'y'],
        'some_other_property': [
            { 'some_property': 'x' }
        ]
    }

    x = ContainerData.__from_dict__(dct)
    assert x.some_property == ('x', 'y')
    assert x.some_other_property[0].some_property == 'x'

def test_from_dict_sequence_using_typing():
    Data = type(
        'Data',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': str
            }
        }
    )
    ContainerData = type(
        'ContainerMessage',
        (SystemData,),
        {
            '__annotations__': {
                'some_property': typing.Tuple[str, ...],
                'some_other_property': typing.Tuple[Data, ...]
            }
        }
    )

    dct = {
        'some_property': ['x', 'y'],
        'some_other_property': [
            { 'some_property': 'x' }
        ]
    }

    x = ContainerData.__from_dict__(dct)
    assert x.some_property == ('x', 'y')
    assert x.some_other_property[0].some_property == 'x'

def test_from_dict_fails():
    with pytest.raises(TypeError):
        type(
            'Message',
            (SystemData,),
            {
                '__annotations__': {
                    'some_property': typing.Union[str, int]
                }
            }
        )
    with pytest.raises(TypeError):
        type(
            'Message',
            (SystemData,),
            {
                '__annotations__': {
                    'some_property': tuple[str, str]
                }
            }
        )

def test_immutable():
    x = SystemData()

    with pytest.raises(AttributeError):
        x.some_property = 'x'
    
def test_exists_repr():
    x = SystemData()
    assert hasattr(x, '__repr__')

def test_exists_str():
    x = SystemData()
    assert hasattr(x, '__str__')

def test_fail_if_str_annotations():
    with pytest.raises(TypeError):
        type(
            'Message',
            (SystemData,),
            {
                '__annotations__': {
                    'some_property': 'str'
                }
            }
        )