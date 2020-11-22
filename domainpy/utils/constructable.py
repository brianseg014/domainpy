
class Constructable:
    
    def __init__(self, *args, **kwargs):
        if hasattr(self.__class__, '__annotations__'):
            attrs = self.__class__.__dict__['__annotations__']
            
            args_count = len(args)
            
            kwargs0 = {}
            
            current_arg = 0
            for k in attrs:
                if current_arg <= args_count - 1:
                    kwargs0[k] = args[current_arg]
                else:
                    try:
                        kwargs0[k] = kwargs[k]
                    except KeyError:
                        raise TypeError('Missing argument for ' + k)
                current_arg = current_arg + 1
                
            self.__dict__.update(**kwargs0)
