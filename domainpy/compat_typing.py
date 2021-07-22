import sys

if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import *  # noqa
else:  # pragma: no cover
    from typing import *  # noqa
    from typing_extensions import (  # noqa
        TypedDict,
        Protocol,
        get_origin,
        get_args,
    )
