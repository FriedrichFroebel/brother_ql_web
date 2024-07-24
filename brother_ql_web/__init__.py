from __future__ import annotations

import logging
from typing import Any


def patch_deprecation_warning() -> None:
    """
    Avoid the deprecation warning from `brother_ql.devicedependent`. This has been
    fixed in the Git version, but not in the PyPI version:
    https://github.com/pklaus/brother_ql/commit/5c2b72b18bcf436c116f180a9147cbb6805958f5
    """
    original_logger = logging.getLogger("brother_ql.devicedependent").warning

    def warn(message: str, *args: Any, **kwargs: Any) -> None:
        if (
            message
            == "deprecation warning: brother_ql.devicedependent is deprecated and will be removed in a future release"  # noqa: E501
        ):
            return
        original_logger(message, *args, **kwargs)

    logging.getLogger("brother_ql.devicedependent").warn = warn  # type: ignore[assignment,method-assign,attr-defined,unused-ignore]  # noqa: E501


patch_deprecation_warning()


import brother_ql.conversion  # noqa: E402
import PIL  # noqa: E402


# Renamed in version 2.7.0:
# https://pillow.readthedocs.io/en/stable/releasenotes/2.7.0.html#antialias-renamed-to-lanczos
brother_ql.conversion.Image.ANTIALIAS = PIL.Image.LANCZOS  # type: ignore[attr-defined]


__all__: list[str] = []
