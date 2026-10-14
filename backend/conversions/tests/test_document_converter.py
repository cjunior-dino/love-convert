import tempfile
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from conversions.services import (
    ConversionDependencyError,
    DocumentConversionError,
    DocumentConverter,
)


class DocumentConverterTests(SimpleTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("conversions.services.document_converter.shutil.which", return_value=None)
    def test_docx_to_pdf_requires_libreoffice(self, _which):
        input_path = self.output_dir / "input.docx"
        input_path.write_bytes(b"docx")

        with self.assertRaises(ConversionDependencyError) as context:
            DocumentConverter().convert(input_path, "pdf", self.output_dir)

        self.assertIn("LibreOffice", str(context.exception))

    @patch(
        "conversions.services.document_converter.shutil.which",
        side_effect=["/usr/bin/libreoffice", None],
    )
    @patch("conversions.services.document_converter.subprocess.run")
    def test_docx_to_pdf_uses_libreoffice_headless(self, run, _which):
        input_path = self.output_dir / "input.docx"
        input_path.write_bytes(b"docx")
        run.side_effect = lambda *_args, **_kwargs: (
            self.output_dir / "input.pdf"
        ).write_bytes(b"pdf")

        with patch.object(DocumentConverter, "_convert_with_pandoc") as pandoc:
            output = DocumentConverter().convert(
                input_path, "pdf", self.output_dir
            )

        pandoc.assert_not_called()
        command = run.call_args.args[0]
        self.assertEqual(command[0], "/usr/bin/libreoffice")
        self.assertIn("--headless", command)
        self.assertIn("pdf:writer_pdf_Export", command)
        self.assertEqual(command[-1], str(input_path))
        self.assertEqual(run.call_args.kwargs["timeout"], 120)
        self.assertEqual(output.name, "output.pdf")
        self.assertTrue(output.is_file())
        self.assertFalse((self.output_dir / "input.pdf").exists())

    @patch(
        "conversions.services.document_converter.shutil.which",
        side_effect=["/usr/bin/libreoffice", None],
    )
    @patch("conversions.services.document_converter.subprocess.run")
    def test_docx_to_pdf_reports_libreoffice_failure(self, run, _which):
        input_path = self.output_dir / "input.docx"
        input_path.write_bytes(b"docx")
        run.side_effect = subprocess.CalledProcessError(
            1, ["libreoffice"], stderr="falha de conversão"
        )

        with self.assertRaises(DocumentConversionError) as context:
            DocumentConverter().convert(input_path, "pdf", self.output_dir)

        self.assertIn("falha de conversão", str(context.exception))

    @patch.dict("sys.modules", {"pdf2docx": MagicMock()})
    def test_pdf_to_docx_generates_expected_file(self):
        import pdf2docx

        input_path = self.output_dir / "input.pdf"
        input_path.write_bytes(b"%PDF")
        converter = pdf2docx.Converter.return_value
        converter.convert.side_effect = lambda output: Path(output).write_bytes(b"docx")

        output = DocumentConverter().convert(input_path, "docx", self.output_dir)

        pdf2docx.Converter.assert_called_once_with(str(input_path))
        converter.convert.assert_called_once_with(str(output))
        converter.close.assert_called_once()
        self.assertEqual(output.name, "output.docx")
