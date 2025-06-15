"""
notanumber - Store bytes in fp16 floats through creative abuse.

Come with me and you'll be in a world of pure imagination.
"""

from .core import (
    encode,
    decode,
    demo,
    to_zero,
    from_zero,
    to_inf,
    from_inf,
    to_nan,
    from_nan,
    to_subnormal,
    from_subnormal,
)

__version__ = "0.2.0"
__all__ = [
    "encode",
    "decode",
    "demo",
    "to_zero",
    "from_zero",
    "to_inf",
    "from_inf",
    "to_nan",
    "from_nan",
    "to_subnormal",
    "from_subnormal",
]
