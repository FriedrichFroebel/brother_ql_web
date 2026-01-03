from __future__ import annotations

from importlib.resources import as_file, files
from tempfile import NamedTemporaryFile
from unittest import mock

from brother_ql.backends.generic import BrotherQLBackendGeneric
from brother_ql.labels import FormFactor
from brother_ql.raster import BrotherQLRaster
from brother_ql_web import labels
from brother_ql_web.configuration import Font
from PIL import Image, ImageChops, ImageFont

from tests import TestCase


class LabelParametersTestCase(TestCase):
    def test_kind(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            label_size="38",
        )
        self.assertEqual(FormFactor.ENDLESS, parameters.kind)
        parameters.label_size = "62x29"
        self.assertEqual(FormFactor.DIE_CUT, parameters.kind)

    def test_scale_margin(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_size=37,
            margin_top=10,
            margin_bottom=25,
            margin_left=33,
            margin_right=57,
        )
        self.assertEqual(3, parameters.margin_top_scaled)  # 3.7
        self.assertEqual(9, parameters.margin_bottom_scaled)  # 9.25
        self.assertEqual(12, parameters.margin_left_scaled)  # 12.21
        self.assertEqual(21, parameters.margin_right_scaled)  # 21.09

    def test_fill_color(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            label_size="62",
        )
        self.assertEqual((0, 0, 0), parameters.fill_color)
        parameters.label_size = "62red"
        self.assertEqual((255, 0, 0), parameters.fill_color)

    def test_font_path(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_family=None,
            font_style=None,
        )
        parameters.configuration.label.default_font = Font(
            family="DejaVu Serif", style="Book"
        )

        # 1) Fallback to default.
        self.assertEqual(
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", parameters.font_path
        )

        # 2) Retrieve existing.
        parameters.font_family = "Roboto"
        parameters.font_style = "Medium"
        self.assertEqual(
            "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Medium.ttf",
            parameters.font_path,
        )

        # 3) Retrieve missing.
        parameters.font_family = "Custom family"
        parameters.font_style = "Regular"
        with self.assertRaisesRegex(
            expected_exception=LookupError,
            expected_regex=r"^Couldn't find the font & style$",
        ):
            parameters.font_path

    def test_width_height(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
        )

        # 1) Unknown label size.
        parameters.label_size = "1337"
        with self.assertRaisesRegex(
            expected_exception=LookupError, expected_regex=r"^Unknown label_size$"
        ):
            parameters.width_height

        # 2) Width > height. Handle standard and rotated.
        parameters.label_size = "62x29"
        self.assertEqual((696, 271), parameters.width_height)
        self.assertEqual(696, parameters.width)
        self.assertEqual(271, parameters.height)

        parameters.orientation = "rotated"
        self.assertEqual((271, 696), parameters.width_height)
        self.assertEqual(271, parameters.width)
        self.assertEqual(696, parameters.height)

        # 3) Height > width. Handle standard and rotated.
        parameters.label_size = "39x48"
        parameters.orientation = "standard"
        self.assertEqual((495, 425), parameters.width_height)
        self.assertEqual(495, parameters.width)
        self.assertEqual(425, parameters.height)

        parameters.orientation = "rotated"
        self.assertEqual((425, 495), parameters.width_height)
        self.assertEqual(425, parameters.width)
        self.assertEqual(495, parameters.height)

        # 4) Endless labels.
        parameters.label_size = "62"
        parameters.orientation = "standard"
        self.assertEqual((696, 0), parameters.width_height)
        self.assertEqual(696, parameters.width)
        self.assertEqual(0, parameters.height)

        parameters.orientation = "rotated"
        self.assertEqual((0, 696), parameters.width_height)
        self.assertEqual(0, parameters.width)
        self.assertEqual(696, parameters.height)


class DetermineImageDimensionsTestCase(TestCase):
    def test_determine_image_dimensions(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_family="Roboto",
            font_style="Medium",
        )
        image_font = ImageFont.truetype(parameters.font_path, parameters.font_size)
        text = "Test text"

        # 1) Fixed size labels.
        parameters.label_size = "62x29"
        parameters.orientation = "standard"
        result = labels._determine_image_dimensions(
            text=text, image_font=image_font, parameters=parameters
        )
        self.assertEqual((696, 271, 391, 72), result)

        parameters.orientation = "rotated"
        result = labels._determine_image_dimensions(
            text=text, image_font=image_font, parameters=parameters
        )
        self.assertEqual((271, 696, 391, 72), result)

        # 2) Endless labels.
        parameters.label_size = "62"
        parameters.orientation = "standard"
        result = labels._determine_image_dimensions(
            text=text, image_font=image_font, parameters=parameters
        )
        self.assertEqual((696, 141, 391, 72), result)

        parameters.orientation = "rotated"
        result = labels._determine_image_dimensions(
            text=text, image_font=image_font, parameters=parameters
        )
        self.assertEqual((461, 696, 391, 72), result)


class DetermineTextOffsetsTestCase(TestCase):
    def test_determine_text_offsets(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_family="Roboto",
            font_style="Medium",
        )

        # 1) Die cut/fixed size label.
        parameters.label_size = "62x29"
        parameters.orientation = "standard"
        result = labels._determine_text_offsets(
            height=271, width=696, text_height=72, text_width=391, parameters=parameters
        )
        self.assertEqual((152, 88), result)

        parameters.orientation = "rotated"
        result = labels._determine_text_offsets(
            width=271, height=696, text_height=72, text_width=391, parameters=parameters
        )
        self.assertEqual((0, 301), result)

        # 2) Endless label.
        parameters.label_size = "62"
        parameters.orientation = "standard"
        result = labels._determine_text_offsets(
            height=141, width=696, text_height=72, text_width=391, parameters=parameters
        )
        self.assertEqual((152, 24), result)

        parameters.orientation = "rotated"
        result = labels._determine_text_offsets(
            height=696, width=461, text_height=72, text_width=391, parameters=parameters
        )
        self.assertEqual((35, 301), result)


class CreateLabelImageTestCase(TestCase):
    def test_create_label_image(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_family="Roboto",
            font_style="Medium",
            text="Hello World!",
            label_size="62",
        )
        image = labels.create_label_image(parameters)
        self.addCleanup(image.close)
        reference = files("tests") / "data" / "hello_world.png"
        with as_file(reference) as path:
            with Image.open(path) as target_image:
                self.assertEqual(target_image.mode, image.mode)
                self.assertEqual(target_image.size, image.size)
                difference = ImageChops.difference(target_image, image)
                for index, pixel in enumerate(difference.get_flattened_data()):
                    self.assertEqual((0, 0, 0), pixel, index)

    def test_create_label_image__multiline_text(self) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_family="DejaVu Serif",
            font_style="Book",
            text="Hello World!\r\n\nLorem ipsum",
            label_size="62",
        )
        image = labels.create_label_image(parameters)
        self.addCleanup(image.close)
        reference = files("tests") / "data" / "multiline.png"
        with as_file(reference) as path:
            with Image.open(path) as target_image:
                self.assertEqual(target_image.mode, image.mode)
                self.assertEqual(target_image.size, image.size)
                difference = ImageChops.difference(target_image, image)
                for index, pixel in enumerate(difference.get_flattened_data()):
                    self.assertEqual((0, 0, 0), pixel, index)


class ImageToPngBytesTestCase(TestCase):
    def test_image_to_png_bytes(self) -> None:
        reference = files("tests") / "data" / "hello_world.png"
        with as_file(reference) as path:
            with Image.open(path) as image:
                actual = labels.image_to_png_bytes(image)
            expected = path.read_bytes()
        self.assertEqual(expected, actual)


class GenerateLabelTestCase(TestCase):
    @mock.patch("brother_ql.raster.logger.warning")
    @mock.patch("brother_ql.conversion.logger.warning")
    def test_generate_label(self, _: mock.Mock, __: mock.Mock) -> None:
        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
            font_family="Roboto",
            font_style="Medium",
            text="Hello World!",
        )

        # 1) Save image.
        with NamedTemporaryFile(suffix=".png") as save_to:
            result = labels.generate_label(
                parameters=parameters,
                configuration=parameters.configuration,
                save_image_to=save_to.name,
            )
            reference = files("tests") / "data" / "hello_world.png"
            with as_file(reference) as path:
                save_to.seek(0)
                self.assertEqual(path.read_bytes(), save_to.read())
        self.assertTrue(result.data)

        # 2) Endless label with standard orientation.
        parameters.label_size = "62"
        parameters.orientation = "standard"
        result = labels.generate_label(
            parameters=parameters, configuration=parameters.configuration
        )
        reference = (
            files("tests") / "data" / "hello_world__label_size_62__standard.data"
        )
        with as_file(reference) as path:
            self.assertEqual(path.read_bytes(), result.data)

        # 3) Endless label with rotated orientation.
        parameters.label_size = "62"
        parameters.orientation = "rotated"
        result = labels.generate_label(
            parameters=parameters, configuration=parameters.configuration
        )
        reference = files("tests") / "data" / "hello_world__label_size_62__rotated.data"
        with as_file(reference) as path:
            self.assertEqual(path.read_bytes(), result.data)

        # 4) Die cut label.
        for orientation in ["standard", "rotated"]:
            with self.subTest(orientation=orientation):
                parameters.label_size = "62x29"
                parameters.orientation = orientation
                result = labels.generate_label(
                    parameters=parameters,
                    configuration=parameters.configuration,
                )
                reference = (
                    files("tests")
                    / "data"
                    / f"hello_world__label_size_62x29__{orientation}.data"
                )
                with as_file(reference) as path:
                    self.assertEqual(path.read_bytes(), result.data)

        # 5) Red mode.
        parameters.label_size = "62red"
        parameters.orientation = "standard"
        parameters.configuration.printer.model = "QL-800"
        result = labels.generate_label(
            parameters=parameters, configuration=parameters.configuration
        )
        reference = (
            files("tests") / "data" / "hello_world__label_size_62red__standard.data"
        )
        with as_file(reference) as path:
            self.assertEqual(path.read_bytes(), result.data)


class PrintLabelTestCase(TestCase):
    def test_print_label(self) -> None:
        class Backend(BrotherQLBackendGeneric):
            def __init__(self, device_specifier: str) -> None:
                pass

        parameters = labels.LabelParameters(
            configuration=self.example_configuration,
        )
        qlr = BrotherQLRaster()
        qlr.data = b"My dummy data"

        # 1) One label.
        parameters.label_count = 1
        with (
            mock.patch.object(labels.logger, "info") as info_mock,
            mock.patch.object(Backend, "write") as write_mock,
        ):
            labels.print_label(
                parameters=parameters,
                qlr=qlr,
                configuration=parameters.configuration,
                backend_class=Backend,
            )
        info_mock.assert_called_once_with("Printing label %d of %d ...", 1, 1)
        write_mock.assert_called_once_with(b"My dummy data")

        # 2) Multiple labels.
        parameters.label_count = 5
        with (
            mock.patch.object(labels.logger, "info") as info_mock,
            mock.patch.object(Backend, "write") as write_mock,
        ):
            labels.print_label(
                parameters=parameters,
                qlr=qlr,
                configuration=parameters.configuration,
                backend_class=Backend,
            )
        info_mock.assert_has_calls(
            [mock.call("Printing label %d of %d ...", i, 5) for i in range(1, 6)],
            any_order=False,
        )
        self.assertEqual(5, info_mock.call_count, info_mock.call_args_list)
        write_mock.assert_has_calls([mock.call(b"My dummy data")] * 5)
        self.assertEqual(5, write_mock.call_count, write_mock.call_args_list)
