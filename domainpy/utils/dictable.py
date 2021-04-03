
import inspect

class Dictable:
    
    @classmethod
    def __from_dict__(cls, dictionary):
        if hasattr(cls, '__annotations__'):
            attrs = cls.__dict__['__annotations__']
            
            kwargs0 = {}
            for k in attrs:
                expected_type = attrs[k]
                
                value = dictionary[k]
                
                if hasattr(expected_type, '__origin__') and expected_type.__origin__ in (tuple, list):
                    (expected_type0,) = expected_type.__args__
                    kwargs0[k] = expected_type.__origin__(
                        expected_type0.__from_dict__(v) 
                        for v in value
                    )
                elif expected_type in (str, int, float, bool):
                    if expected_type == int and isinstance(value, str):
                        kwargs0[k] = int(value)
                    elif expected_type == float and isinstance(value, (str, int)):
                        kwargs0[k] = float(value)
                    elif isinstance(value, expected_type):
                        kwargs0[k] = expected_type(value)
                    else:
                        raise TypeError(f'{k} should be type of {expected_type}, found {value.__class__.__name__}')
                elif isinstance(value, dict):
                    if Dictable in expected_type.mro():
                        kwargs0[k] = expected_type.__from_dict__(value)
                    else:
                        raise TypeError(f'{k} should be Dictable, found {expected_type}')
                else:
                    raise TypeError(f'{k} should be type of dict, found {expected_type}')
                
            return cls(**kwargs0)
        else:
            raise NotImplementedError(
                f'{cls.__name__} should have annotations'
            )
    
    def __to_dict__(self):
        if hasattr(self.__class__, '__annotations__'):
            attrs = self.__class__.__dict__['__annotations__']
            
            dictionary = {}
            for k in attrs:
                
                expected_type = attrs[k]
                
                value = self.__dict__[k]
                
                if hasattr(expected_type, '__origin__') and expected_type.__origin__ in (list, tuple):
                    (expected_type0,) = expected_type.__args__
                    if not all(isinstance(v, expected_type0) for v in value):
                        raise TypeError(f'{k} should be type {expected_type.__origin__.__class__.__name__}[{expected_type0}]')
                elif not isinstance(value, expected_type):
                    raise TypeError(f'{k} should be type {expected_type} by declaration, found {value.__class__.__name__}')
                
                if hasattr(expected_type, '__origin__') and expected_type.__origin__ in (list, tuple):
                    (expected_type0,) = expected_type.__args__

                    if issubclass(expected_type0, Dictable):
                        dictionary[k] = expected_type.__origin__(v.__to_dict__() for v in value)
                        
                elif isinstance(value, (str, int, float, bool)):
                    dictionary[k] = value
                elif isinstance(value, tuple):
                    dictionary[k] = tuple(v.__to_dict__() for v in value)
                elif isinstance(value, list):
                    dictionary[k] = list(v.__to_dict__() for v in value)
                elif isinstance(value, Dictable):
                    dictionary[k] = value.__to_dict__()
                else:
                    raise TypeError(f'{k} in {self.__class__.__name__} should be dictable or list/tuple (is {expected_type})')

            return dictionary
        else:
            raise KeyError(
                f'{self.__class__.__name__} should have annotations'
            )