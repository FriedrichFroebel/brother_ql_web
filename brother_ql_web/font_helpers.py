from __future__ import annotations

import logging
import subprocess
from collections import defaultdict


logger = logging.getLogger(__name__)
del logging


def get_fonts(folder: str | None = None) -> dict[str, dict[str, str]]:
    """
    Scan a folder (or the system) for .ttf / .otf fonts and
    return a dictionary of the structure  family -> style -> file path
    """
    if _has_fontra():
        return _get_fonts_using_fontra(folder)
    return _get_fonts_using_fontconfig(folder)


def _get_fonts_using_fontconfig(folder: str | None = None) -> dict[str, dict[str, str]]:
    fonts: dict[str, dict[str, str]] = defaultdict(dict)
    if folder:
        cmd = ["fc-scan", "--format", "%{file}:%{family}:style=%{style}\n", folder]
    else:
        cmd = ["fc-list", ":", "file", "family", "style"]
    for line in subprocess.check_output(cmd).decode("utf-8").split("\n"):
        line = line.strip()
        if not line:
            continue
        if "otf" not in line and "ttf" not in line:
            continue
        parts = line.split(":")
        if "style=" not in line or len(parts) < 3:
            # fc-list did not output all desired properties
            logger.warning("skipping invalid font %s", line)
            continue
        path = parts[0]
        families = parts[1].strip().split(",")
        styles = parts[2].split("=")[1].split(",")
        if len(families) == 1 and len(styles) > 1:
            families = [families[0]] * len(styles)
        elif len(families) > 1 and len(styles) == 1:
            styles = [styles[0]] * len(families)
        if len(families) != len(styles):
            logger.debug("Problem with this font: %s", line)
            continue
        for i in range(len(families)):
            fonts[families[i]][styles[i]] = path
            # logger.debug("Added this font: %s", (families[i], styles[i], path))
    return dict(fonts)


def _has_fontra() -> bool:
    from importlib.util import find_spec

    return find_spec("fontra") is not None


def _get_fonts_using_fontra(folder: str | None = None) -> dict[str, dict[str, str]]:
    from pathlib import Path
    import fontra

    if folder:
        fontra.FONTDIRS_CUSTOM.append(Path(folder))
        fontra.update_custom_fontfiles_index()
        fontra.update_fontrefs_index()
    else:
        fontra.init_fontdb()
    fonts: dict[str, dict[str, str]] = defaultdict(dict)
    families = fontra.all_fonts(classical=True)
    for family in families:
        styles = fontra.get_font_styles(family, classical=True)
        for style in styles:
            path: str = (
                fontra.get_font(family, style, classical=True)
                .path.absolute()
                .as_posix()
            )
            fonts[family][style] = path
    return dict(fonts)
