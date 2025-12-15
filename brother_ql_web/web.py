from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import bottle
from brother_ql import BrotherQLRaster

from brother_ql_web.configuration import Configuration
from brother_ql_web.labels import (
    LabelParameters,
    create_label_image,
    image_to_png_bytes,
    generate_label,
    print_label,
)
from brother_ql_web.utils import BACKEND_TYPE


logger = logging.getLogger(__name__)
del logging

CURRENT_DIRECTORY = Path(__file__).parent


def get_config(key: str) -> object:
    return bottle.request.app.config[key]


@bottle.route("/")  # type: ignore[untyped-decorator]
def index() -> None:
    bottle.redirect("/labeldesigner")


@bottle.route("/static/<filename:path>")  # type: ignore[untyped-decorator]
def serve_static(filename: str) -> bottle.HTTPResponse:
    return bottle.static_file(filename, root=str(CURRENT_DIRECTORY / "static"))


@bottle.route("/labeldesigner")  # type: ignore[untyped-decorator]
@bottle.jinja2_view("labeldesigner.jinja2")  # type: ignore[untyped-decorator]
def labeldesigner() -> dict[str, Any]:
    fonts = cast(dict[str, dict[str, str]], get_config("brother_ql_web.fonts"))
    font_family_names = sorted(list(fonts.keys()))
    configuration = cast(Configuration, get_config("brother_ql_web.configuration"))
    return {
        "font_family_names": font_family_names,
        "fonts": fonts,
        "label_sizes": get_config("brother_ql_web.label_sizes"),
        "website": configuration.website,
        "label": configuration.label,
        "default_orientation": configuration.label.default_orientation,
    }


def _save_to_bytes(upload: bottle.FileUpload | None) -> bytes | None:
    if upload is None:
        return None
    output = BytesIO()
    upload.save(output)
    output.seek(0)
    return output.getvalue()


def get_label_parameters(
    request: bottle.BaseRequest, should_be_file: bool = False
) -> LabelParameters:
    # As we have strings, *bottle* would try to generate Latin-1 bytes from it
    # before decoding it back to UTF-8. This seems to break some umlauts, thus
    # resulting in UnicodeEncodeErrors being raised when going back to UTF-8.
    # For now, we just state that we always receive clean UTF-8 data and thus
    # the recode operations just can be omitted. All external API users are
    # responsible for passing clean data.
    # References:
    #   * https://github.com/bottlepy/bottle/blob/99341ff3791b2e7e705d7373e71937e9018eb081/bottle.py#L2197-L2203  # noqa: E501
    #   * https://github.com/FriedrichFroebel/brother_ql_web/issues/9
    parameters = request.params
    parameters.recode_unicode = False
    d = parameters.decode()  # UTF-8 decoded form data

    try:
        font_family = d.get("font_family").rpartition("(")[0].strip()
        font_style = d.get("font_family").rpartition("(")[2].rstrip(")")
    except AttributeError:
        if should_be_file:
            font_family = ""
            font_style = ""
        else:
            raise ValueError(
                "Could not find valid font specifier. Please pass the `font_family` "
                "parameter with the family and style in the format `Roboto (Medium)`, "
                "where Roboto is the family name and Medium the corresponding font "
                "style."
            )
    context = {
        "text": d.get("text", ""),
        "image": _save_to_bytes(request.files.get("image")),
        "pdf": _save_to_bytes(request.files.get("pdf")),
        "font_size": int(d.get("font_size", 100)),
        "font_family": font_family,
        "font_style": font_style,
        "label_size": d.get("label_size", "62"),
        "margin": int(d.get("margin", 10)),
        "threshold": int(d.get("threshold", 70)),
        "align": d.get("align", "center"),
        "orientation": d.get("orientation", "standard"),
        "margin_top": int(d.get("margin_top", 24)),
        "margin_bottom": int(d.get("margin_bottom", 45)),
        "margin_left": int(d.get("margin_left", 35)),
        "margin_right": int(d.get("margin_right", 35)),
        "label_count": int(d.get("label_count", 1)),
        "high_quality": bool(d.get("high_quality", False)),  # TODO: Enable by default.
        "configuration": request.app.config["brother_ql_web.configuration"],
    }

    return LabelParameters(**context)


@bottle.get("/api/preview/text")  # type: ignore[untyped-decorator]
@bottle.post("/api/preview/text")  # type: ignore[untyped-decorator]
def get_preview_image() -> bytes:
    parameters = get_label_parameters(bottle.request)
    image = create_label_image(parameters=parameters)
    return_format = bottle.request.query.get("return_format", "png")
    if return_format == "base64":
        import base64

        bottle.response.set_header("Content-type", "text/plain")
        return base64.b64encode(image_to_png_bytes(image))
    else:
        bottle.response.set_header("Content-type", "image/png")
        return image_to_png_bytes(image)


@bottle.post("/api/print/text")  # type: ignore[untyped-decorator]
@bottle.get("/api/print/text")  # type: ignore[untyped-decorator]
def print_text() -> dict[str, bool | str]:
    """
    API to print some text

    returns: JSON
    """
    return_dict: dict[str, bool | str] = {"success": False}

    try:
        parameters = get_label_parameters(bottle.request)
    except (AttributeError, LookupError, ValueError) as e:
        return_dict["error"] = str(e)
        return return_dict

    if parameters.text is None:
        return_dict["error"] = "Please provide the text for the label"
        return return_dict

    qlr = generate_label(
        parameters=parameters,
        configuration=cast(Configuration, get_config("brother_ql_web.configuration")),
        save_image_to="sample-out.png" if bottle.DEBUG else None,
    )

    return _print(parameters=parameters, qlr=qlr)


@bottle.post("/api/print/image")  # type: ignore[untyped-decorator]
def print_image() -> dict[str, bool | str]:
    """
    API to print an image

    returns: JSON
    """
    return_dict: dict[str, bool | str] = {"success": False}

    try:
        parameters = get_label_parameters(bottle.request, should_be_file=True)
    except (AttributeError, LookupError, ValueError) as e:
        return_dict["error"] = str(e)
        return return_dict

    if parameters.image is None or not parameters.image:
        return_dict["error"] = "Please provide the label image"
        return return_dict

    qlr = generate_label(
        parameters=parameters,
        configuration=cast(Configuration, get_config("brother_ql_web.configuration")),
    )

    return _print(parameters=parameters, qlr=qlr)


def _print(parameters: LabelParameters, qlr: BrotherQLRaster) -> dict[str, bool | str]:
    return_dict: dict[str, bool | str] = {"success": False}

    if not bottle.DEBUG:
        try:
            print_label(
                parameters=parameters,
                qlr=qlr,
                configuration=cast(
                    Configuration, get_config("brother_ql_web.configuration")
                ),
                backend_class=cast(
                    BACKEND_TYPE,
                    get_config("brother_ql_web.backend_class"),
                ),
            )
        except Exception as e:
            return_dict["message"] = str(e)
            logger.warning("Exception happened: %s", e)
            return return_dict

    return_dict["success"] = True
    if bottle.DEBUG:
        return_dict["data"] = str(qlr.data)
    return return_dict


def main(
    configuration: Configuration,
    fonts: dict[str, dict[str, str]],
    label_sizes: list[tuple[str, str]],
    backend_class: BACKEND_TYPE,
) -> None:
    app = bottle.default_app()
    app.config["brother_ql_web.configuration"] = configuration
    app.config["brother_ql_web.fonts"] = fonts
    app.config["brother_ql_web.label_sizes"] = label_sizes
    app.config["brother_ql_web.backend_class"] = backend_class
    bottle.TEMPLATE_PATH.append(CURRENT_DIRECTORY / "views")
    debug = configuration.server.is_in_debug_mode
    app.run(host=configuration.server.host, port=configuration.server.port, debug=debug)
