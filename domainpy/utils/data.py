
import sys
import typing
import inspect
import typeguard
import itertools
import collections


class Field:

    __slots__ = [
        'name',
        'type',
        'default'
    ]

    def __init__(self, name, type, default):
        self.name = name
        self.type = type
        self.default = default

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name}, type={self.type}, default={self.default})'


class MISSING:
    pass


def create_fn(fnname, txt, cls, globals, locals):
    globals = { k:v for k,v in globals.items() }
    globals['typeguard'] = typeguard
    globals['typing'] = typing

    local_args = ', '.join(locals.keys())
    txt = f'def __create_fn__({local_args}):\n{txt}\n return {fnname}'

    ns = {}
    exec(txt, globals, ns)
    
    fn = ns['__create_fn__'](**locals)

    if hasattr(fn, '__name__'):
        fn.__qualname__ = f'{cls.__qualname__}.{fn.__name__}'

    return fn


def get_fields(cls):
    fields: dict[str, Field] = collections.OrderedDict()
    for cls in itertools.chain(cls.__bases__, [cls]):
        cls_annotations = cls.__dict__.get('__annotations__')
        if cls_annotations:
            for a_name, a_type in cls_annotations.items():
                if type(a_type) == str:
                    raise TypeError(f'annotation {a_name} in {cls.__name__} is str')

                # If ClassVar, ignore
                if typing.get_origin(a_type) == typing.get_origin(typing.ClassVar[typing.Any]):
                    continue

                f = Field(a_name, a_type, getattr(cls, a_name, MISSING))
                fields[f.name] = f

    return fields.values()


def create_init_fn(cls, fields: list[Field]):
    fnname = '__init__'

    globals = sys.modules[cls.__module__].__dict__
    locals = {}
    
    # If have default, will be ommitted in __init__
    # still can pass the arg as kwarg
    init_fields = [f for f in fields if not f.default is not MISSING]

    if len(init_fields) > 0:
        locals = { f'_type_{f.name}': f.type for f in init_fields }

        args = (f'{f.name}:_type_{f.name}' for f in init_fields)

        # Assignment for immutable self
        assignments = (f'  self.__dict__.update({{ "{f.name}": {f.name} }})' for f in init_fields)

        args = ', '.join(itertools.chain(['self'], args, ['**kwargs']))

        body = '\n'.join(itertools.chain(assignments, ['  self.__dict__.update(kwargs)']))

        txt = f' def {fnname}({args}):\n{body}'
        txt = f' @typeguard.typechecked\n{txt}'
    else:
        txt = f' def {fnname}(self, **kwargs):\n  self.__dict__.update(kwargs)'
    
    return create_fn(fnname, txt, cls, globals, locals)


def create_fromdict_fn(cls, fields: list[Field]):
    fnname = '__from_dict__'

    globals = sys.modules[cls.__module__].__dict__
    locals = {}

    dctcode = []
    for f in fields:
        # Field is one of three types
        # raw (str, int...), list/tuple[str, ...], or has __from_dict__

        # typing: str
        if f.type in (str, int, float, bool):

            locals.update({ f'_type_{f.name}': f.type })

            dctcode.append(f'  "{f.name}": _type_{f.name}(dct["{f.name}"])')

        # typing: tuple[str]
        # typing: tuple[SystemMessage]
        elif f.type in (list, tuple) or typing.get_origin(f.type) in (list, tuple):

            origin = typing.get_origin(f.type) or f.type
            origin_args = typing.get_args(f.type)

            locals.update({ f'_type_{f.name}': origin })

            if len(origin_args) == 2 and origin_args[-1] == Ellipsis:
                tuple_arg = origin_args[0]

                locals.update({ f'_type_{f.name}_i_': tuple_arg })

                if tuple_arg in (str, int, float, bool):
                    dctcode.append(f'  "{f.name}": _type_{f.name}([_type_{f.name}_i_(i) for i in dct["{f.name}"]])')
                elif '__from_dict__' in dir(tuple_arg):
                    dctcode.append(f'  "{f.name}": _type_{f.name}([_type_{f.name}_i_.__from_dict__(i_dct) for i_dct in dct["{f.name}"]])')
                else:
                    raise TypeError(f'{f.type}: unsupported type in list/tuple')
            else:
                raise TypeError('list/tuple should have one typing arg and ellipsis')

        # typing: Optional[str]
        # typing: Optional[SystemMessage]
        elif '__args__' in dir(f.type): # All typing except tuple,list
            
            origin = typing.get_origin(f.type)
            origin_args = typing.get_args(f.type)

            if origin is typing.Union:
                if len(origin_args) == 2 and origin_args[-1] == type(None):
                    union_arg = origin_args[0]
                    
                    locals.update({ f'_type_{f.name}': union_arg })

                    if union_arg in (str, int, float, bool):
                        dctcode.append(f'  "{f.name}": _type_{f.name}(dct["{f.name}"]) if dct["{f.name}"] is not None else None')
                    elif '__from_dict__' in dir(union_arg):
                        dctcode.append(f'  "{f.name}": _type_{f.name}.__from_dict__(dct["{f.name}"]) if dct["{f.name}"] is not None else None')
                else:
                    raise TypeError('only typing.Optional is support from typing')
            else:
                raise TypeError('only typing.Optional is support from typing')

        # typing: SystemMessage
        elif '__from_dict__' in dir(f.type):

            locals.update({ f'_type_{f.name}': f.type })
            
            dctcode.append(f'  "{f.name}": _type_{f.name}.__from_dict__(dct["{f.name}"])')

        else:
            raise TypeError(
                f'{f.type} ({type(f.type)}) unsupported type. Support types are: '
                f'SystemMessage, str, int, float, bool, tuple, list and typing.Optional'
            )

    dct = '{' + ','.join(dctcode) + '}'

    txt = f' @classmethod\n def {fnname}(cls, dct: dict) -> "{cls.__name__}":\n  return cls(**{dct})'

    return create_fn(fnname, txt, cls, globals, locals)

def create_todict_fn(cls, field):
    fnname = '__to_dict__'

    globals = sys.modules[cls.__module__].__dict__
    locals = {}

    code = [
        f'',
        f'  dct = {{}}',
        f'  for f_name,f_value in self.__dict__.items():',
        f'   if hasattr(f_value, "__to_dict__"):',
        f'    dct[f_name] = f_value.__to_dict__()',
        f'   elif isinstance(f_value, (list, tuple)):',
        f'    dct[f_name] = []',
        f'    for i in f_value:',
        f'     if hasattr(f_value, "__to_dict__"):',
        f'      dct[f_name].append(f_value.__to_dict__())',
        f'     else:',
        f'      dct[f_name].append(f_value)',
        f'   else:',
        f'    dct[f_name] = f_value'
    ]
    body = '\n'.join(code)

    txt = f' def {fnname}(self):\n  {body}\n  return dct'

    return create_fn(fnname, txt, cls, globals, locals)


def create_setattr_fn(cls):
    fnname = '__setattr__'

    globals = sys.modules[cls.__module__].__dict__

    body = '  raise AttributeError("attributes are read-only")'

    txt = f' def {fnname}(self, key, value):\n{body}'

    return create_fn(fnname, txt, cls, globals, {})


def create_delattr_fn(cls):
    fnname = '__delattr__'

    globals = sys.modules[cls.__module__].__dict__

    body = '  raise AttributeError("attributes are read-only")'

    txt = f' def {fnname}(self, name: str) -> None:\n{body}'

    return create_fn(fnname, txt, cls, globals, {})


def create_repr_fn(cls, fields):
    fnname = '__repr__'

    globals = sys.modules[cls.__module__].__dict__
    
    init_fields = [f for f in fields if not f.default is not MISSING]

    args = ', '.join(f'{f.name}={{self.{f.name}!r}}' for f in init_fields)
    txt = f' def {fnname}(self):\n  return f"{{self.__class__.__name__}}({args})"'
    
    return create_fn(fnname, txt, cls, globals, {})


def create_str_fn(cls, fields):
    fnname = '__str__'

    globals = sys.modules[cls.__module__].__dict__

    args = ', '.join(f'{f.name}={{self.{f.name}!r}}' for f in fields)
    txt = f' def {fnname}(self):\n  return f"{{self.__class__.__name__}}({args})"'
    
    return create_fn(fnname, txt, cls, globals, {})



class system_data(type):
    
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        
        fields = get_fields(new_cls)

        if '__init__' not in new_cls.__dict__:
            setattr(new_cls, '__init__', create_init_fn(new_cls, fields))

        if '__setattr__' not in new_cls.__dict__:
            setattr(new_cls, '__setattr__', create_setattr_fn(new_cls))

        if '__delattr__' not in new_cls.__dict__:
            setattr(new_cls, '__delattr__', create_delattr_fn(new_cls))

        if '__from_dict__' not in new_cls.__dict__:
            setattr(new_cls, '__from_dict__', create_fromdict_fn(new_cls, fields))

        if '__to_dict__' not in new_cls.__dict__:
            setattr(new_cls, '__to_dict__', create_todict_fn(new_cls, fields))

        if '__repr__' not in new_cls.__dict__:
            setattr(new_cls, '__repr__', create_repr_fn(new_cls, fields))

        if '__str__' not in new_cls.__dict__:
            setattr(new_cls, '__str__', create_str_fn(new_cls, fields))
        
        return new_cls

class SystemData(metaclass=system_data):
    pass