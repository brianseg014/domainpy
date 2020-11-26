
class Constructable:
    
    def __init__(self, *args, **kwargs):
        if hasattr(self.__class__, '__annotations__'):
            attrs = self.__class__.__dict__['__annotations__']
            
            args_count = len(args)
            
            kwargs0 = {}
            
            current_arg = 0
            for k in attrs:
                expected_value_type = attrs[k]
                
                if current_arg <= args_count - 1:
                    value = args[current_arg]
                    if isinstance(value, expected_value_type):
                        kwargs0[k] = value
                    else:
                        raise TypeError(f'{k} should be instance of {expected_value_type}, found ' + value.__class__.__name__)
                else:
                    try:
                        value = kwargs[k]
                        if isinstance(value, expected_value_type):
                            kwargs0[k] = value
                        else:
                            raise TypeError(f'{k} should be instance of {expected_value_type}, found ' + value.__class__.__name__)
                    except KeyError:
                        raise TypeError('Missing argument for ' + k)
                current_arg = current_arg + 1
                
            self.__dict__.update(**kwargs0)
