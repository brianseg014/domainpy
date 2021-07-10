

def to_dict(obj):
    if not hasattr(obj, '__dict__'):
        return obj

    dictionary = {}
    for k,v in obj.__dict__.items():
        if k.startswith('_'):
            continue
        if isinstance(v, (list, tuple)):
            element = []
            for i in v:
                element.append(to_dict(i))
        else:
            element = to_dict(v)
        dictionary[k] = element
    return dictionary

def from_dict(cls, args, path=''):
    if Dictable not in cls.mro():
        if hasattr(cls, '__origin__'):

            origin = cls.__origin__
            origin_args = cls.__args__
            if origin in (list, tuple):
                if len(origin_args) == 1: # Every position of sequence with same type
                    return origin([from_dict(origin_args[0], a, path) for a in args])
                else: # Every position of sequence with its own type
                    return origin([from_dict(oa, a, path) for oa,a in zip(origin_args, args)])
            else:
                raise Exception(f'unsupported type {cls} with duck typing')
            
        else:

            return cls(args)
    
    kwargs = {}
    cls_annotations = cls.__dict__.get('__annotations__', {})
    if len(cls_annotations) > 0:
        for a_name,a_type in cls_annotations.items():
            if a_name not in args:
                raise KeyError(f'missing {a_name} in {path}')
            kwargs[a_name] = from_dict(a_type, args[a_name], f'{path}.{a_name}')
    return cls(**kwargs)


class Dictable:

    def __to_dict__(self):
        return to_dict(self)

    @classmethod
    def __from_dict__(cls, dictionary):
        return from_dict(cls, dictionary, '$')

    def __str__(self):
        return f'{self.__class__.__name__}({self.__to_dict__()})'