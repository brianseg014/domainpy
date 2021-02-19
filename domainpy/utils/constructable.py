
class Constructable:
    
    def __init__(self, *args, **kwargs):
        if hasattr(self.__class__, '__annotations__'):
            annotations = self.__class__.__dict__['__annotations__']
            
            args_count = len(args)
            
            kwargs0 = {}
            
            current_arg = 0
            for k in annotations:
                expected_type = annotations[k]
                
                if current_arg <= args_count - 1:
                    value = args[current_arg]
                else:
                    try:
                        value = kwargs[k]
                    except KeyError:
                        raise TypeError(f'Missing argument {k} for '
                                    f'{self.__class__.__name__}')
                
                if hasattr(expected_type, '__origin__') and expected_type.__origin__ in (list, tuple):
                    (expected_type0,) = expected_type.__args__
                    for v in value:
                        if not isinstance(v, expected_type0):
                            raise TypeError(f'Bad type in {k}: Value {v} expected to be {expected_type0}')
                    
                    kwargs0[k] = value
                elif isinstance(value, expected_type):
                    kwargs0[k] = value
                else:
                    raise TypeError(f'Class {self.__class__.__name__}: {k} should be instance of {expected_type},'
                                    f' found {value.__class__.__name__}')
                
                current_arg = current_arg + 1
                
            self.__dict__.update(**kwargs0)
