from __future__ import annotations

from unittest import TestCase

from brother_ql_web.font_helpers import get_fonts


class GetFontsTestCase(TestCase):
    # Reference: https://packages.ubuntu.com/lunar/all/fonts-roboto-unhinted/filelist
    ROBOTO_FILES = {
        "Roboto": {
            "Thin": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Thin.ttf",  # noqa: E501
            "Medium Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-MediumItalic.ttf",  # noqa: E501
            "Thin Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-ThinItalic.ttf",  # noqa: E501
            "Light Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-LightItalic.ttf",  # noqa: E501
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Italic.ttf",  # noqa: E501
            "Black Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-BlackItalic.ttf",  # noqa: E501
            "Medium": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Medium.ttf",  # noqa: E501
            "Bold": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf",  # noqa: E501
            "Black": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf",  # noqa: E501
            "Light": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Light.ttf",  # noqa: E501
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf",  # noqa: E501
            "Bold Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-BoldItalic.ttf",  # noqa: E501
        },
        "Roboto Black": {
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-BlackItalic.ttf",  # noqa: E501
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf",  # noqa: E501
        },
        "Roboto Condensed": {
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Italic.ttf",  # noqa: E501
            "Bold": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Bold.ttf",  # noqa: E501
            "Medium": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Medium.ttf",  # noqa: E501
            "Bold Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-BoldItalic.ttf",  # noqa: E501
            "Light Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-LightItalic.ttf",  # noqa: E501
            "Light": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Light.ttf",  # noqa: E501
            "Medium Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-MediumItalic.ttf",  # noqa: E501
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Regular.ttf",  # noqa: E501
        },
        "Roboto Condensed Light": {
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-LightItalic.ttf",  # noqa: E501
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Light.ttf",  # noqa: E501
        },
        "Roboto Condensed Medium": {
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Medium.ttf",  # noqa: E501
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-MediumItalic.ttf",  # noqa: E501
        },
        "Roboto Light": {
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-LightItalic.ttf",  # noqa: E501
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Light.ttf",  # noqa: E501
        },
        "Roboto Medium": {
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-MediumItalic.ttf",  # noqa: E501
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Medium.ttf",  # noqa: E501
        },
        "Roboto Thin": {
            "Regular": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Thin.ttf",  # noqa: E501
            "Italic": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-ThinItalic.ttf",  # noqa: E501
        },
    }

    def assert_font_dictionary_subset(
        self,
        expected: dict[str, dict[str, str]],
        actual: dict[str, dict[str, str]],
        not_in_name: str = "",
    ) -> None:
        for font_name, font_styles in expected.items():
            self.assertIn(font_name, actual.keys())
            actual_styles = actual[font_name]
            with self.subTest(font_name=font_name):
                for font_style, path in font_styles.items():
                    self.assertIn(font_style, actual_styles)
                    self.assertEqual(path, actual_styles[font_style], font_style)
            if not_in_name:
                self.assertNotIn(not_in_name, font_name)

    def test_get_all(self) -> None:
        fonts = get_fonts()
        self.assert_font_dictionary_subset(expected=self.ROBOTO_FILES, actual=fonts)

    def test_get_from_folder(self) -> None:
        fonts = get_fonts(folder="/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF")
        expected = {
            key: value
            for key, value in self.ROBOTO_FILES.items()
            if "Condensed" not in key
        }
        self.assert_font_dictionary_subset(
            expected=expected, actual=fonts, not_in_name="Condensed"
        )
