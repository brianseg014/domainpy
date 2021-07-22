import sys

if sys.version_info >= (3, 8):
    from typing import *  # noqa
else:
    from typing import *  # noqa
    from typing_extensions import (  # noqa
        TypedDict,
        Protocol,
        get_origin,
        get_args,
    )
