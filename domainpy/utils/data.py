import sys
import itertools
import typeguard
import collections
import domainpy.compat_typing as typing


class ImmutableError(Exception):
    pass


class UnsupportedAnnotationInStrError(Exception):
    pass


class Field:

    __slots__ = ["name", "type", "default"]

    def __init__(self, name: str, type: typing.Type, default: typing.Any):
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
    globals["ImmutableError"] = ImmutableError
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
                    raise UnsupportedAnnotationInStrError(
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


def create_setattr_fn(cls):
    fnname = "__setattr__"

    globals = sys.modules[cls.__module__].__dict__

    args = ["self, key, value"]
    body_lines = ['raise ImmutableError("attributes are read-only")']

    return create_fn(
        fnname, args, body_lines, globals=globals, return_type=None
    )


def create_delattr_fn(cls):
    fnname = "__delattr__"

    globals = sys.modules[cls.__module__].__dict__

    args = ["self, name"]
    body_lines = ['raise ImmutableError("attributes are read-only")']

    return create_fn(
        fnname, args, body_lines, globals=globals, return_type=None
    )


def create_eq_fn(cls, fields):
    fnname = "__eq__"

    globals = sys.modules[cls.__module__].__dict__

    args = ["self", "o"]
    body_lines = [
        "if not isinstance(o, self.__class__):",
        " return False",
        "return self.__dict__ == o.__dict__",
    ]

    return create_fn(
        fnname, args, body_lines, globals=globals, return_type=bool
    )


class system_data(type):
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)

        fields = get_fields(new_cls)

        # Constructable
        if "__init__" not in new_cls.__dict__:
            setattr(new_cls, "__init__", create_init_fn(new_cls, fields))

        # Immutable
        if "__setattr__" not in new_cls.__dict__:
            setattr(new_cls, "__setattr__", create_setattr_fn(new_cls))

        if "__delattr__" not in new_cls.__dict__:
            setattr(new_cls, "__delattr__", create_delattr_fn(new_cls))

        # Equality based on data
        if "__eq__" not in new_cls.__dict__:
            setattr(new_cls, "__eq__", create_eq_fn(new_cls, fields))

        return new_cls


Class = typing.TypeVar("Class")


class SystemData(metaclass=system_data):
    pass
