import sys
import itertools
import typeguard
import collections
import domainpy.compat_typing as typing


class Field:

    __slots__ = ["name", "type", "default"]

    def __init__(self, name, type, default):
        self.name = name
        self.type = type
        self.default = default

    def __repr__(self):  # pragma: no cover
        return (
            f"{self.__class__.__name__}("
            f"  name={self.name}, type={self.type}, default={self.default}"
            ")"
        )


class MISSING:
    pass


def create_fn(
    fnname,
    args,
    body_lines,
    *,
    globals={},
    locals={},
    return_type=MISSING,
    decorators=[],
):
    globals = {k: v for k, v in globals.items()}
    globals["typeguard"] = typeguard
    globals["typing"] = typing

    return_annotation = ""
    if return_type is not MISSING:
        locals["_return_type"] = return_type
        return_annotation = " -> _return_type"

    args = ", ".join(args)
    body = "\n".join(f"  {line}" for line in body_lines)

    decorators = "\n".join(f" {d}" for d in decorators)
    txt = f"{decorators}\n def {fnname}({args}){return_annotation}:\n{body}"

    local_args = ", ".join(locals.keys())
    txt = f"def __create_fn__({local_args}):\n{txt}\n return {fnname}"

    ns = {}
    exec(txt, globals, ns)
    return ns["__create_fn__"](**locals)


def get_fields(cls):
    fields: typing.OrderedDict[str, Field] = collections.OrderedDict()
    for cls in itertools.chain(cls.__bases__, [cls]):
        cls_annotations = cls.__dict__.get("__annotations__")
        if cls_annotations:
            for a_name, a_type in cls_annotations.items():
                if type(a_type) == str:
                    raise TypeError(
                        f"annotation {a_name} in {cls.__name__} is str"
                    )

                # If ClassVar, ignore
                if typing.get_origin(a_type) == typing.get_origin(
                    typing.ClassVar[typing.Any]
                ):
                    continue

                f = Field(a_name, a_type, getattr(cls, a_name, MISSING))
                fields[f.name] = f

    return fields.values()


def create_init_fn(cls, fields: typing.List[Field]):
    fnname = "__init__"

    globals = sys.modules[cls.__module__].__dict__
    locals = {}

    # If have default, will be ommitted in __init__
    # still can pass the arg as kwarg
    init_fields = [f for f in fields if f.default is MISSING]

    args: typing.List[str] = []
    body_lines: typing.List[str] = []

    if len(init_fields) > 0:
        locals = {f"_type_{f.name}": f.type for f in init_fields}

        args.extend(f"{f.name}:_type_{f.name}" for f in init_fields)

        # Assignment for immutable self
        body_lines.extend(
            f'self.__dict__.update({{ "{f.name}": {f.name} }})'
            for f in init_fields
        )

    return create_fn(
        fnname,
        ["self"] + args + ["**kwargs"],
        body_lines + ["self.__dict__.update(kwargs)"],
        globals=globals,
        locals=locals,
        return_type=None,
        decorators=["@typeguard.typechecked"],
    )


def create_fromdict_fn(cls, fields: typing.List[Field]):
    fnname = "__from_dict__"

    globals = sys.modules[cls.__module__].__dict__
    locals = {}

    body_lines = []

    dctcode = []
    for f in fields:
        # Field is one of three types
        # raw (str, int...), list/typing.Tuple[str, ...], or has __from_dict__

        # typing: str
        if f.type in (str, int, float, bool):

            locals.update({f"_type_{f.name}": f.type})

            dctcode.append(f'  "{f.name}": _type_{f.name}(dct["{f.name}"])')

        # typing: typing.Tuple[str]
        # typing: typing.Tuple[SystemMessage]
        elif f.type in (list, tuple) or typing.get_origin(f.type) in (
            list,
            tuple,
        ):

            origin = typing.get_origin(f.type) or f.type
            origin_args = typing.get_args(f.type)

            locals.update({f"_type_{f.name}": origin})

            if len(origin_args) == 2 and origin_args[-1] == Ellipsis:
                tuple_arg = origin_args[0]

                locals.update({f"_type_{f.name}_i_": tuple_arg})

                if tuple_arg in (str, int, float, bool):
                    dctcode.append(
                        f'  "{f.name}": '
                        f"      _type_{f.name}(["
                        f'          _type_{f.name}_i_(i) for i in dct["{f.name}"]'  # noqa: E501
                        "       ])"
                    )
                elif "__from_dict__" in dir(tuple_arg):
                    dctcode.append(
                        f'  "{f.name}": '
                        f"      _type_{f.name}(["
                        f"          _type_{f.name}_i_.__from_dict__(i_dct) "
                        f'          for i_dct in dct["{f.name}"]'
                        "       ])"
                    )
                else:
                    raise TypeError(
                        f"{f.type}: unsupported type in list/tuple"
                    )
            else:
                raise TypeError(
                    "list/tuple should have one typing arg and ellipsis"
                )

        # typing: Optional[str]
        # typing: Optional[SystemMessage]
        elif "__args__" in dir(f.type):  # All typing except tuple,list

            origin = typing.get_origin(f.type)
            origin_args = typing.get_args(f.type)

            if origin is typing.Union:
                # fmt: off
                optional_args_signature = (
                    len(origin_args) == 2
                    and origin_args[-1] == type(None)  # noqa: E721
                )
                # fmt: on
                if optional_args_signature:

                    union_arg = origin_args[0]

                    locals.update({f"_type_{f.name}": union_arg})

                    if union_arg in (str, int, float, bool):
                        dctcode.append(
                            f'  "{f.name}": '
                            f'      _type_{f.name}(dct["{f.name}"]) '
                            f'      if dct["{f.name}"] is not None '
                            f"      else None"
                        )
                    elif "__from_dict__" in dir(union_arg):
                        dctcode.append(
                            f'  "{f.name}": '
                            f'      _type_{f.name}.__from_dict__(dct["{f.name}"]) '  # noqa: E501
                            f'      if dct["{f.name}"] is not None '
                            "       else None"
                        )
                else:
                    raise TypeError(
                        "only typing.Optional is support from typing"
                    )
            else:
                raise TypeError("only typing.Optional is support from typing")

        # typing: SystemMessage
        elif "__from_dict__" in dir(f.type):

            locals.update({f"_type_{f.name}": f.type})

            dctcode.append(
                f'  "{f.name}": _type_{f.name}.__from_dict__(dct["{f.name}"])'
            )

        else:
            raise TypeError(
                f"{f.type} ({type(f.type)}) unsupported. Support types are: "
                "SystemMessage, str, int, float, bool, tuple, list and "
                "typing.Optional"
            )

    dct = "{" + ",".join(dctcode) + "}"

    body_lines.append(f"return cls(**{dct})")

    return create_fn(
        fnname,
        ["cls", "dct: dict"],
        body_lines,
        globals=globals,
        locals=locals,
        return_type=cls,
        decorators=["@classmethod"],
    )


def create_todict_fn(cls, field):
    fnname = "__to_dict__"

    globals = sys.modules[cls.__module__].__dict__
    locals = {}

    body_lines = [
        "",
        "dct = {}",
        "for f_name,f_value in self.__dict__.items():",
        ' if hasattr(f_value, "__to_dict__"):',
        "  dct[f_name] = f_value.__to_dict__()",
        " elif isinstance(f_value, (list, tuple)):",
        "  dct[f_name] = []",
        "  for i in f_value:",
        '   if hasattr(f_value, "__to_dict__"):',
        "    dct[f_name].append(f_value.__to_dict__())",
        "   else:",
        "    dct[f_name].append(f_value)",
        " else:",
        "  dct[f_name] = f_value",
        "return dct",
    ]

    return create_fn(
        fnname,
        ["self"],
        body_lines,
        globals=globals,
        locals=locals,
        return_type=dict,
    )


def create_setattr_fn(cls):
    fnname = "__setattr__"

    globals = sys.modules[cls.__module__].__dict__

    args = ["self, key, value"]
    body_lines = ['raise AttributeError("attributes are read-only")']

    return create_fn(
        fnname, args, body_lines, globals=globals, return_type=None
    )


def create_delattr_fn(cls):
    fnname = "__delattr__"

    globals = sys.modules[cls.__module__].__dict__

    args = ["self, name"]
    body_lines = ['raise AttributeError("attributes are read-only")']

    return create_fn(
        fnname, args, body_lines, globals=globals, return_type=None
    )


def create_repr_fn(cls, fields):
    fnname = "__repr__"

    globals = sys.modules[cls.__module__].__dict__

    init_fields = [f for f in fields if f.default is MISSING]

    expression = ", ".join(
        f"{f.name}={{self.{f.name}!r}}" for f in init_fields
    )

    body_lines = []
    body_lines.append(
        'return f"{self.__class__.__name__}(' + expression + ')"'
    )

    return create_fn(
        fnname, ["self"], body_lines, globals=globals, return_type=str
    )


def create_str_fn(cls, fields):
    fnname = "__str__"

    globals = sys.modules[cls.__module__].__dict__

    expression = ", ".join(f"{f.name}={{self.{f.name}!r}}" for f in fields)

    body_lines = []
    body_lines.append(
        'return f"{self.__class__.__name__}(' + expression + ')"'
    )

    return create_fn(
        fnname, ["self"], body_lines, globals=globals, return_type=str
    )


class system_data(type):
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)

        fields = get_fields(new_cls)

        if "__init__" not in new_cls.__dict__:
            setattr(new_cls, "__init__", create_init_fn(new_cls, fields))

        if "__setattr__" not in new_cls.__dict__:
            setattr(new_cls, "__setattr__", create_setattr_fn(new_cls))

        if "__delattr__" not in new_cls.__dict__:
            setattr(new_cls, "__delattr__", create_delattr_fn(new_cls))

        if "__from_dict__" not in new_cls.__dict__:
            setattr(
                new_cls, "__from_dict__", create_fromdict_fn(new_cls, fields)
            )

        if "__to_dict__" not in new_cls.__dict__:
            setattr(new_cls, "__to_dict__", create_todict_fn(new_cls, fields))

        if "__repr__" not in new_cls.__dict__:
            setattr(new_cls, "__repr__", create_repr_fn(new_cls, fields))

        if "__str__" not in new_cls.__dict__:
            setattr(new_cls, "__str__", create_str_fn(new_cls, fields))

        return new_cls


Class = typing.TypeVar("Class")


class SystemData(metaclass=system_data):
    def __to_dict__(self) -> dict:
        return super().__to_dict__()  # type: ignore

    @classmethod
    def __from_dict__(cls: typing.Type[Class], dct: dict) -> Class:
        return super().__from_dict__(cls, dict)  # type: ignore
