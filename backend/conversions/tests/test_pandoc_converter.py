import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from conversions.services import (
    PandocConversionError,
    PandocConverter,
    PandocNotFoundError,
)


class PandocConverterTests(SimpleTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.input_path = self.output_dir / "input.docx"
        self.input_path.write_bytes(b"docx")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("conversions.services.pandoc_converter.shutil.which", return_value=None)
    def test_missing_executable_raises_clear_error(self, _which):
        with self.assertRaises(PandocNotFoundError):
            PandocConverter().convert(self.input_path, "markdown", self.output_dir)

    @patch("conversions.services.pandoc_converter.shutil.which", return_value="pandoc")
    @patch("conversions.services.pandoc_converter.subprocess.run")
    def test_uses_safe_markdown_command(self, run, _which):
        def create_output(command, **kwargs):
            (self.output_dir / "output.md").write_text("# ok", encoding="utf-8")

        run.side_effect = create_output
        PandocConverter().convert(self.input_path, "markdown", self.output_dir)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "pandoc")
        self.assertIn("--to=gfm", command)
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertTrue(run.call_args.kwargs["check"])
        self.assertEqual(run.call_args.kwargs["timeout"], 60)

    @patch("conversions.services.pandoc_converter.shutil.which", return_value="pandoc")
    @patch("conversions.services.pandoc_converter.subprocess.run")
    def test_subprocess_error_is_wrapped(self, run, _which):
        run.side_effect = subprocess.CalledProcessError(
            1, ["pandoc"], stderr="documento corrompido"
        )
        with self.assertRaises(PandocConversionError) as context:
            PandocConverter().convert(self.input_path, "html", self.output_dir)
        self.assertIn("documento corrompido", str(context.exception))
