from __future__ import annotations

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files  # type: ignore[import-not-found,no-redef]  # noqa: E501
import base64
import os
import subprocess
from tempfile import NamedTemporaryFile
from threading import Thread
from time import sleep
from typing import cast
from unittest import mock

import requests
from brother_ql_web import web
from brother_ql_web.labels import LabelParameters

from tests import TestCase as _TestCase


class TestCase(_TestCase):
    process: subprocess.Popen[bytes] | None = None
    thread: Thread | None = None
    printer_file: str | None = None

    def setUp(self) -> None:
        super().setUp()
        self.process = None
        self.thread = None
        self.printer_file = None

    def tearDown(self) -> None:
        super().tearDown()
        if self.process:
            self.process.kill()
            if self.process.stdout:
                self.process.stdout.close()
            if self.process.stderr:
                self.process.stderr.close()
            self.process.wait()
        if self.thread:
            self.thread.join()
        if self.printer_file:
            os.unlink(self.printer_file)

    def run_server(self, log_level: str = "") -> None:
        self.printer_file = NamedTemporaryFile(delete=False).name

        def run() -> None:
            self.process = subprocess.Popen(
                [
                    "python",
                    "-m",
                    "brother_ql_web",
                    "--configuration",
                    self.example_configuration_path,
                    f"file://{self.printer_file}",
                ]
                + (["--log-level", log_level] if log_level else []),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.thread = Thread(target=run)
        self.thread.start()
        sleep(2.0)


class GetConfigTestCase(TestCase):
    pass


class IndexTestCase(TestCase):
    def test_index(self) -> None:
        self.run_server()
        response = requests.get("http://localhost:8013/", allow_redirects=False)
        self.assertEqual(303, response.status_code)
        self.assertEqual(
            "http://localhost:8013/labeldesigner", response.headers["Location"]
        )


class ServeStaticTestCase(TestCase):
    def test_serve_static(self) -> None:
        self.run_server()
        response = requests.get("http://localhost:8013/static/css/custom.css")
        self.assertEqual(200, response.status_code)
        reference = files("brother_ql_web") / "static" / "css" / "custom.css"
        with as_file(reference) as path:
            self.assertEqual(path.read_bytes(), response.content)


class LabeldesignerTestCase(TestCase):
    def test_labeldesigner(self) -> None:
        self.run_server()
        response = requests.get("http://localhost:8013/labeldesigner")
        self.assertEqual(200, response.status_code)
        self.assertIn(b"DejaVu Serif", response.content)


class GetLabelParametersTestCase(TestCase):
    def test_all_params_set(self) -> None:
        request = mock.Mock()
        request.params.decode.return_value = dict(
            font_family="DejaVu Serif (Book)",
            text="Hello World!",
            font_size="70",
            label_size="42",
            margin="13",
            threshold="50",
            align="left",
            orientation="rotated",
            margin_top="10",
            margin_bottom="20",
            margin_left="37",
            margin_right="38",
            label_count="20",
            high_quality="True",
        )
        request.app.config = {
            "brother_ql_web.configuration": self.example_configuration
        }

        parameters = web.get_label_parameters(request)
        self.assertEqual(
            LabelParameters(
                configuration=self.example_configuration,
                font_family="DejaVu Serif",
                font_style="Book",
                text="Hello World!",
                font_size=70,
                label_size="42",
                margin=13,
                threshold=50,
                align="left",
                orientation="rotated",
                margin_top=10,
                margin_bottom=20,
                margin_left=37,
                margin_right=38,
                label_count=20,
                high_quality=True,
                image=b"",
                pdf=b"",
            ),
            parameters,
        )

    def test_mostly_default_params_values(self) -> None:
        request = mock.Mock()
        request.params.decode.return_value = dict(font_family="Roboto (Regular)")
        request.app.config = {
            "brother_ql_web.configuration": self.example_configuration
        }

        parameters = web.get_label_parameters(request)
        self.assertEqual(
            LabelParameters(
                configuration=self.example_configuration,
                font_family="Roboto",
                font_style="Regular",
                text="",
                font_size=100,
                label_size="62",
                margin=10,
                threshold=70,
                align="center",
                orientation="standard",
                margin_top=24,
                margin_bottom=45,
                margin_left=35,
                margin_right=35,
                label_count=1,
                high_quality=False,
                image=b"",
                pdf=b"",
            ),
            parameters,
        )


class GetPreviewImageTestCase(TestCase):
    def test_base64(self) -> None:
        self.run_server()
        response = requests.get(
            "http://localhost:8013/api/preview/text?"
            "return_format=base64&text=Hello%20World!&"
            "label_size=62&font_family=Roboto%20(Medium)"
        )
        self.assertEqual(200, response.status_code)
        reference = files("tests") / "data" / "hello_world.png"
        with as_file(reference) as path:
            decoded = base64.b64decode(response.content)
            self.assertEqual(path.read_bytes(), decoded)

    def test_plain_bytes(self) -> None:
        self.run_server()
        response = requests.get(
            "http://localhost:8013/api/preview/text?"
            "return_format=png&text=Hello%20World!&"
            "label_size=62&font_family=Roboto%20(Medium)"
        )
        self.assertEqual(200, response.status_code)
        reference = files("tests") / "data" / "hello_world.png"
        with as_file(reference) as path:
            self.assertEqual(path.read_bytes(), response.content)

    def test_special_characters(self) -> None:
        self.run_server()
        # Minimal copy from the Firefox developer tools.
        headers = {
            "Content-Type": "multipart/form-data; boundary=---------------------------381934621323024354152349680295"  # noqa: E501
        }
        body = """\r
-----------------------------381934621323024354152349680295\r
Content-Disposition: form-data; name="text"\r
\r
abcdefgö+ëŠ\r
-----------------------------381934621323024354152349680295\r
Content-Disposition: form-data; name="font_family"\r
\r
Roboto (Medium)\r
-----------------------------381934621323024354152349680295\r
Content-Disposition: form-data; name="label_size"\r
\r
62\r
-----------------------------381934621323024354152349680295--\r
""".encode()
        response = requests.post(
            "http://localhost:8013/api/preview/text?return_format=png",
            data=body,
            headers=headers,
        )
        self.assertEqual(200, response.status_code, response.content)
        self.assertLessEqual(14000, len(response.content))  # 14061 bytes


class PrintTextTestCase(TestCase):
    def test_error(self) -> None:
        self.run_server()
        response = requests.get("http://localhost:8013/api/print/text")
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            (
                b'{"success": false, '
                b'"error": "Could not find valid font specifier. '
                b"Please pass the `font_family` parameter with the family and style "
                b"in the format `Roboto (Medium)`, where Roboto is the family name "
                b'and Medium the corresponding font style."}'
            ),
            response.content,
        )
        with open(cast(str, self.printer_file), mode="rb") as fd:
            self.assertEqual(b"", fd.read())

    def test_debug_mode(self) -> None:
        reference = files("tests") / "data" / "print_text__debug_mode.json"
        with as_file(reference) as path:
            expected = path.read_bytes()

        self.run_server(log_level="DEBUG")
        response = requests.get(
            "http://localhost:8013/api/print/text?"
            "text=Hello%20World!&label_size=62&"
            "font_family=Roboto%20(Medium)&orientation=standard"
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected, response.content)
        with open(cast(str, self.printer_file), mode="rb") as fd:
            self.assertEqual(b"", fd.read())

    def test_regular_mode(self) -> None:
        reference = (
            files("tests") / "data" / "hello_world__label_size_62__standard.data"
        )
        with as_file(reference) as path:
            expected = path.read_bytes()

        self.run_server()
        response = requests.get(
            "http://localhost:8013/api/print/text?"
            "text=Hello%20World!&label_size=62&"
            "font_family=Roboto%20(Medium)&orientation=standard"
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'{"success": true}', response.content)
        with open(cast(str, self.printer_file), mode="rb") as fd:
            self.assertEqual(expected, fd.read())


class PrintImageTestCase(TestCase):
    def test_error__empty_image(self) -> None:
        self.run_server()
        response = requests.post(
            url="http://localhost:8013/api/print/image", files={"image": b""}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            b'{"success": false, "error": "Please provide the label image"}',
            response.content,
        )
        with open(cast(str, self.printer_file), mode="rb") as fd:
            self.assertEqual(b"", fd.read())

    def test_error__no_image(self) -> None:
        self.run_server()
        response = requests.post(url="http://localhost:8013/api/print/image")
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            b'{"success": false, "error": "Please provide the label image"}',
            response.content,
        )
        with open(cast(str, self.printer_file), mode="rb") as fd:
            self.assertEqual(b"", fd.read())

    def test_print_image(self) -> None:
        image = files("tests") / "data" / "hello_world.png"
        reference = (
            files("tests") / "data" / "hello_world__label_size_62__standard.data"
        )
        with as_file(image) as path:
            image_data = path.read_bytes()
            expected = reference.read_bytes()

        self.run_server()
        response = requests.post(
            url=(
                "http://localhost:8013/api/print/image?"
                "label_size=62&orientation=standard"
            ),
            files={"image": image_data},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'{"success": true}', response.content)
        with open(cast(str, self.printer_file), mode="rb") as fd:
            self.assertEqual(expected, fd.read())


class MainTestCase(TestCase):
    pass
