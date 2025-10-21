from __future__ import annotations

import json
from dataclasses import dataclass, field as dataclass_field, fields as dataclass_fields
from typing import Any, cast


@dataclass
class Configuration:
    server: ServerConfiguration
    printer: PrinterConfiguration
    label: LabelConfiguration
    website: WebsiteConfiguration

    @classmethod
    def from_json(cls, json_file: str) -> Configuration:
        with open(json_file) as fd:
            parsed: dict[str, Any] = json.load(fd)
        kwargs: dict[str, Any] = {}
        global_variables = globals()
        for field in dataclass_fields(cls):
            name: str = field.name
            field_type: str = cast(str, field.type)
            field_class = global_variables[field_type]
            kwargs_inner = parsed.pop(name, None)
            if name == "printer" and not kwargs_inner:
                raise ValueError("Printer configuration missing")
            if not kwargs_inner:
                instance = field_class()
            else:
                instance = field_class(**kwargs_inner)
            kwargs[name] = instance
        if parsed:
            raise ValueError(f"Unknown configuration values: {parsed}")
        return cls(**kwargs)

    def to_json(self) -> str:
        return json.dumps(self, indent=2, default=lambda o: o.__dict__)


@dataclass
class ServerConfiguration:
    port: int = 8013
    host: str = ""
    log_level: str = "WARNING"
    additional_font_folder: str = ""

    @property
    def is_in_debug_mode(self) -> bool:
        return self.log_level == "DEBUG"


@dataclass
class PrinterConfiguration:
    model: str
    printer: str


@dataclass(frozen=True)
class Font:
    family: str
    style: str


@dataclass
class LabelConfiguration:
    default_size: str = "62"
    default_orientation: str = "standard"
    default_font_size: int = 70
    default_fonts: list[Font] = dataclass_field(default_factory=list)
    default_font: Font | None = None

    def __post_init__(self) -> None:
        self.default_fonts = [
            font if isinstance(font, Font) else Font(**font)
            for font in self.default_fonts
        ]


@dataclass
class WebsiteConfiguration:
    html_title: str = "Label Designer"
    page_title: str = "Brother QL Label Designer"
    page_headline: str = "Design your label and print it…"
