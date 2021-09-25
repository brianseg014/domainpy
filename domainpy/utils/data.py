import sys
import inspect
import collections
import typeguard
import domainpy.compat_typing as typing


class ImmutableError(Exception):
    pass


class UnsupportedAnnotationInStrError(Exception):
    pass


class Field:

    __slots__ = ["name", "type", "default"]

    def __init__(
        self, name: str, type: typing.Type, default: typing.Any
    ):  # pylint: disable=redefined-builtin
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
    cls_globals=None,
    cls_locals=None,
    return_type=MISSING,
    decorators=None,
):
    if cls_globals is None:
        cls_globals = {}

    if cls_locals is None:
        cls_locals = {}

    if decorators is None:
        decorators = []

    cls_globals = dict(cls_globals.items())
    cls_globals["ImmutableError"] = ImmutableError
    cls_globals["typeguard"] = typeguard
    cls_globals["typing"] = typing

    return_annotation = ""
    if return_type is not MISSING:
        cls_locals["_return_type"] = return_type
        return_annotation = " -> _return_type"

    args = ", ".join(args)
    body = "\n".join(f"  {line}" for line in body_lines)

    decorators = "\n".join(f" {d}" for d in decorators)
    txt = f"{decorators}\n def {fnname}({args}){return_annotation}:\n{body}"

    local_args = ", ".join(cls_locals.keys())
    txt = f"def __create_fn__({local_args}):\n{txt}\n return {fnname}"

    exec_locals = {}
    exec(txt, cls_globals, exec_locals)  # pylint: disable=exec-used
    return exec_locals["__create_fn__"](**cls_locals)


def get_fields(cls):
    fields: typing.OrderedDict[str, Field] = collections.OrderedDict()
    for current_cls in inspect.getmro(cls)[::-1]:
        cls_annotations = current_cls.__dict__.get("__annotations__")
        if cls_annotations:
            for a_name, a_type in cls_annotations.items():
                if a_name == '__topic__':
                    continue

                if isinstance(a_type, str):
                    raise UnsupportedAnnotationInStrError(
                        f"annotation {a_name} in {current_cls.__name__} is str"
                    )

                # If ClassVar, ignore
                if typing.get_origin(a_type) is typing.get_origin(
                    typing.ClassVar[typing.Any]
                ):
                    continue

                field = Field(
                    a_name, a_type, getattr(current_cls, a_name, MISSING)
                )
                fields[field.name] = field

    return fields.values()


def create_init_fn(cls, fields: typing.List[Field]):
    fnname = "__init__"

    cls_globals = sys.modules[cls.__module__].__dict__
    cls_locals = {}

    # If have default, will be ommitted in __init__
    # still can pass the arg as kwarg
    init_fields = [f for f in fields if f.default is MISSING]

    args: typing.List[str] = []
    body_lines: typing.List[str] = []

    if len(init_fields) > 0:
        cls_locals = {f"_type_{f.name}": f.type for f in init_fields}

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
        cls_globals=cls_globals,
        cls_locals=cls_locals,
        return_type=None,
        decorators=["@typeguard.typechecked"],
    )


def create_setattr_fn(cls):
    fnname = "__setattr__"

    cls_globals = sys.modules[cls.__module__].__dict__

    args = ["self, key, value"]
    body_lines = ['raise ImmutableError("attributes are read-only")']

    return create_fn(
        fnname, args, body_lines, cls_globals=cls_globals, return_type=None
    )


def create_delattr_fn(cls):
    fnname = "__delattr__"

    cls_globals = sys.modules[cls.__module__].__dict__

    args = ["self, name"]
    body_lines = ['raise ImmutableError("attributes are read-only")']

    return create_fn(
        fnname, args, body_lines, cls_globals=cls_globals, return_type=None
    )


def create_eq_fn(cls):
    fnname = "__eq__"

    cls_globals = sys.modules[cls.__module__].__dict__

    args = ["self", "o"]
    body_lines = [
        "if not isinstance(o, self.__class__):",
        " return False",
        "return self.__dict__ == o.__dict__",
    ]

    return create_fn(
        fnname, args, body_lines, cls_globals=cls_globals, return_type=bool
    )


class MetaSystemData(type):
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
            setattr(new_cls, "__eq__", create_eq_fn(new_cls))

        new_cls.__topic__ = new_cls.__name__

        return new_cls


Class = typing.TypeVar("Class")


class SystemData(metaclass=MetaSystemData):
    __topic__: str

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"
