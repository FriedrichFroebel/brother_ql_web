from __future__ import annotations

import json
from tempfile import NamedTemporaryFile
from typing import cast, Union

from brother_ql_web.configuration import (
    Configuration,
    Font,
    LabelConfiguration,
    PrinterConfiguration,
    ServerConfiguration,
    WebsiteConfiguration,
)

from tests import TestCase

CUSTOM_CONFIGURATION = """
{
  "server": {
    "port": 1337,
    "host": "test.local",
    "log_level": "ERROR",
    "additional_font_folder": ""
  },
  "printer": {
    "model": "QL-800",
    "printer": "file:///dev/usb/lp1"
  },
  "label": {
    "default_size": "62",
    "default_orientation": "standard",
    "default_font_size": 42,
    "default_fonts": [
      {
        "family": "Minion Pro",
        "style": "Semibold"
      },
      {
        "family": "Linux Libertine",
        "style": "Regular"
      },
      {
        "family": "DejaVu Serif",
        "style": "Book"
      }
    ],
    "default_font": null
  },
  "website": {
    "html_title": "Label Designer",
    "page_title": "Brother QL Label Designer",
    "page_headline": "Design your label and print it!"
  }
}
"""


class ConfigurationTestCase(TestCase):
    @property
    def example_json(self) -> dict[str, dict[str, str | int | dict[str, str]]]:
        with open(self.example_configuration_path) as fd:
            return cast(
                dict[str, dict[str, Union[str, int, dict[str, str]]]], json.load(fd)
            )

    def test_from_json(self) -> None:
        with NamedTemporaryFile(suffix=".json", mode="w+t") as json_file:
            json_file.write(CUSTOM_CONFIGURATION)
            json_file.seek(0)

            configuration = Configuration.from_json(json_file.name)
            self.assertEqual(
                ServerConfiguration(
                    port=1337,
                    host="test.local",
                    log_level="ERROR",
                    additional_font_folder="",
                ),
                configuration.server,
            )
            self.assertEqual(
                PrinterConfiguration(model="QL-800", printer="file:///dev/usb/lp1"),
                configuration.printer,
            )
            self.assertEqual(
                LabelConfiguration(
                    default_size="62",
                    default_orientation="standard",
                    default_font_size=42,
                    default_fonts=[
                        Font(family="Minion Pro", style="Semibold"),
                        Font(family="Linux Libertine", style="Regular"),
                        Font(family="DejaVu Serif", style="Book"),
                    ],
                    default_font=None,
                ),
                configuration.label,
            )
            self.assertEqual(
                WebsiteConfiguration(
                    html_title="Label Designer",
                    page_title="Brother QL Label Designer",
                    page_headline="Design your label and print it!",
                ),
                configuration.website,
            )

    def test_from_json__too_many_keys(self) -> None:
        with NamedTemporaryFile(suffix=".json", mode="w+t") as json_file:
            data = self.example_json
            data["key"] = {"value": 42}
            json_file.write(json.dumps(data))
            json_file.seek(0)

            with self.assertRaisesRegex(
                ValueError,
                r"^Unknown configuration values: \{'key': \{'value': 42\}\}$",
            ):
                Configuration.from_json(json_file.name)

    def test_from_json__missing_server_key(self) -> None:
        with NamedTemporaryFile(suffix=".json", mode="w+t") as json_file:
            data = self.example_json
            del data["server"]
            json_file.write(json.dumps(data))
            json_file.seek(0)

            configuration = Configuration.from_json(json_file.name)
            self.assertEqual(ServerConfiguration(), configuration.server)

    def test_from_json__missing_printer_key(self) -> None:
        with NamedTemporaryFile(suffix=".json", mode="w+t") as json_file:
            data = self.example_json
            del data["printer"]
            json_file.write(json.dumps(data))
            json_file.seek(0)

            with self.assertRaisesRegex(ValueError, r"^Printer configuration missing$"):
                Configuration.from_json(json_file.name)

    def test_to_json(self) -> None:
        with NamedTemporaryFile(suffix=".json", mode="w+t") as json_file:
            json_file.write(CUSTOM_CONFIGURATION)
            json_file.seek(0)

            configuration = Configuration.from_json(json_file.name)
            self.assertEqual(
                CUSTOM_CONFIGURATION.strip(), configuration.to_json().strip()
            )


class ServerConfigurationTestCase(TestCase):
    def test_is_in_debug_mode(self) -> None:
        self.assertTrue(ServerConfiguration(log_level="DEBUG").is_in_debug_mode)

        for level in ["INFO", "WARNING", "ERROR"]:
            with self.subTest(level=level):
                self.assertFalse(ServerConfiguration(log_level=level).is_in_debug_mode)


class PrinterConfigurationTestCase(TestCase):
    pass


class FontTestCase(TestCase):
    pass


class LabelConfigurationTestCase(TestCase):
    def test_post_init(self) -> None:
        default_fonts: list[Font | dict[str, str]] = [
            Font(family="Font family", style="Regular"),
            {"family": "Another font family", "style": "Bold"},
        ]
        configuration = LabelConfiguration(default_fonts=default_fonts)  # type: ignore[arg-type]  # noqa: E501
        self.assertEqual(
            [
                Font(family="Font family", style="Regular"),
                Font(family="Another font family", style="Bold"),
            ],
            configuration.default_fonts,
        )


class WebsiteConfigurationTestCase(TestCase):
    pass
