
import inspect

class Dictable:
    
    @classmethod
    def __from_dict__(cls, dictionary):
        if hasattr(cls, '__annotations__'):
            attrs = cls.__dict__['__annotations__']
            
            kwargs0 = {}
            for k in attrs:
                expected_value_type = attrs[k]
                
                value = dictionary[k]
                
                if expected_value_type in (str, int, float, bool):
                    if isinstance(value, expected_value_type):
                        kwargs0[k] = expected_value_type(value)
                    else:
                        raise TypeError(f'{k} should be type of {expected_value_type}')
                elif isinstance(value, dict):
                    if Dictable in expected_value_type.mro():
                        kwargs0[k] = expected_value_type.__from_dict__(value)
                    else:
                        raise TypeError(f'{k} should be Dictable, found {expected_value_type}')
                else:
                    raise TypeError(f'{k} should be type of dict, found {expected_value_type}')
                
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
                
                expected_value_type = attrs[k]
                
                value = self.__dict__[k]
                
                if not isinstance(value, expected_value_type):
                    raise TypeError(f'{k} should be type {expected_value_type} by declaration, found {value.__class__.__name__}')
                
                if isinstance(value, (str, int, float, bool)):
                    dictionary[k] = value
                elif isinstance(value, Dictable):
                    dictionary[k] = value.__to_dict__()
                else:
                    raise TypeError(f'{k} in {self.__class__.__name__} should be dictable')
                    
            return dictionary
        else:
            raise KeyError(
                f'{self.__class__.__name__} should have annotations'
            )