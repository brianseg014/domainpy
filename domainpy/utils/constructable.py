from itertools import chain


def create_init_fn(cls):
    fn = '__init__'

    exec_globals = {}

    cls_annotations = cls.__dict__.get('__annotations__', None)
    if cls_annotations:
        cls_annotations = cls.__dict__.get('__annotations__')

        exec_globals = { a_type.__name__: a_type for a_type in cls_annotations.values() }
        
        args = [f'{a_name}: {a_type.__name__}' for a_name,a_type in cls_annotations.items()]
        args = ','.join(chain(['self'], args, ['**kwargs']))

        typechecks = [
            f'  if not isinstance({a_name},{a_type.__name__}):\n   raise TypeError("{a_name} must be type of {a_type.__name__}")' 
            for a_name,a_type in cls_annotations.items()
        ]
        assignments = [
            f'  self.__dict__.update({{"{a_name}": {a_name}}})\n' 
            for a_name in cls_annotations
        ]
        body = '\n'.join(chain(typechecks, assignments, ['  self.__dict__.update(kwargs)']))

        txt = f' def {fn}({args}):\n{body}'
    else:
        txt = f' def {fn}(self, **kwargs):\n  self.__dict__.update(kwargs)'

    txt = f'def __create_fn__():\n{txt}\n return {fn}'

    ns = {}
    exec(txt, exec_globals, ns)
    return ns['__create_fn__']()



class constructable(type):
    
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        new_cls.__init__ = create_init_fn(new_cls)

        return new_cls

class Constructable(metaclass=constructable):
    pass
