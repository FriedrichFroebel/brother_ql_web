from __future__ import annotations

import logging
import random
import sys
from argparse import ArgumentParser, Namespace
from operator import attrgetter
from typing import cast

from brother_ql.labels import ALL_LABELS
from brother_ql.models import ALL_MODELS
from brother_ql_web.configuration import Configuration, Font
from brother_ql_web.utils import collect_fonts

logger = logging.getLogger(__name__)


def log_level_type(value: str) -> int:
    return cast(int, getattr(logging, value.upper()))


def get_parameters() -> Namespace:
    parser = ArgumentParser(
        description=(
            "This is a web service to print labels on Brother QL label printers."
        )
    )
    parser.add_argument("--port", default=False)
    parser.add_argument("--log-level", type=log_level_type, default=False)
    parser.add_argument(
        "--font-folder", default=False, help="folder for additional .ttf/.otf fonts"
    )
    parser.add_argument(
        "--default-label-size",
        default=False,
        help="Label size inserted in your printer. Defaults to 62.",
    )
    parser.add_argument(
        "--default-orientation",
        default=False,
        choices=("standard", "rotated"),
        help=(
            'Label orientation, defaults to "standard". '
            'To turn your text by 90°, state "rotated".'
        ),
    )
    parser.add_argument(
        "--model",
        default=False,
        choices=list(map(attrgetter("identifier"), ALL_MODELS)),
        help="The model of your printer (default: QL-500)",
    )
    parser.add_argument(
        "printer",
        nargs="?",
        default=False,
        help=(
            "String descriptor for the printer to use "
            "(like tcp://192.168.0.23:9100 or file:///dev/usb/lp0)"
        ),
    )
    parser.add_argument(
        "--configuration",
        required=True,
        type=str,
        help="Path to the configuration file to get the basic values from.",
    )

    return parser.parse_args()


class InvalidLabelSize(ValueError):
    pass


class NoFontFound(SystemError):
    pass


def _choose_default_font(
    fonts: dict[str, dict[str, str]], configuration: Configuration
) -> None:
    for font in configuration.label.default_fonts:
        try:
            fonts[font.family][font.style]
            configuration.label.default_font = font
            logger.debug("Selected the following default font: %s", font)
            break
        except KeyError:
            pass
    else:
        sys.stderr.write(
            "Could not find any of the default fonts. Choosing a random one.\n"
        )
        family = random.choice(list(fonts.keys()))
        style = random.choice(list(fonts[family].keys()))
        configuration.label.default_font = Font(family=family, style=style)
        sys.stderr.write(
            f"The default font is now set to: {configuration.label.default_font}\n"
        )


def update_configuration_from_parameters(
    parameters: Namespace, configuration: Configuration
) -> None:
    # Server configuration.
    if parameters.port:
        configuration.server.port = parameters.port
    if parameters.log_level:
        # `log_level` will be numeric if parsed from argv, so we enforce the name here.
        level = parameters.log_level
        configuration.server.log_level = (
            logging.getLevelName(level) if isinstance(level, int) else level
        )
    if parameters.font_folder:
        configuration.server.additional_font_folder = parameters.font_folder

    # Printer configuration.
    if parameters.printer:
        configuration.printer.printer = parameters.printer
    if parameters.model:
        configuration.printer.model = parameters.model

    # Label configuration.
    if parameters.default_label_size:
        configuration.label.default_size = parameters.default_label_size
    if parameters.default_orientation:
        configuration.label.default_orientation = parameters.default_orientation

    # Configuration issues.
    label_sizes = list(map(attrgetter("identifier"), ALL_LABELS))
    if configuration.label.default_size not in label_sizes:
        raise InvalidLabelSize(
            "Invalid default label size. Please choose one of the following:\n"
            + " ".join(label_sizes)
        )

    # System issues.
    fonts = collect_fonts(configuration)
    if not fonts:
        raise NoFontFound(
            "Not a single font was found on your system. "
            'Please install some or use the "--font-folder" argument.\n'
        )

    # Set font data.
    _choose_default_font(fonts=fonts, configuration=configuration)
