import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from conversions.models import Conversion
from conversions.services import ConversionDependencyError, DocumentConversionError


class ConversionApiTests(APITestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=Path(self.temp_dir.name))
        self.settings_override.enable()
        self.url = reverse("conversion-create")

    def tearDown(self):
        self.settings_override.disable()
        self.temp_dir.cleanup()

    @staticmethod
    def docx(name="documento.docx", content=b"docx-content"):
        return SimpleUploadedFile(
            name,
            content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    @staticmethod
    def pdf(name="documento.pdf", content=b"%PDF-1.7"):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    def post(self, file=None, output_format="markdown"):
        data = {"output_format": output_format}
        if file is not None:
            data["file"] = file
        return self.client.post(self.url, data, format="multipart")

    def configure_successful_conversion(self, expected_content):
        def convert(input_path, output_format, output_dir):
            suffixes = {
                "markdown": ".md",
                "html": ".html",
                "pdf": ".pdf",
                "docx": ".docx",
            }
            suffix = suffixes[output_format]
            output = output_dir / f"output{suffix}"
            if output_format in {"markdown", "html"}:
                output.write_text(expected_content, encoding="utf-8")
            else:
                output.write_bytes(b"converted-binary")
            return output

        return patch("conversions.views.DocumentConverter.convert", side_effect=convert)

    def test_upload_without_file(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("arquivo", response.data["error"].lower())

    def test_rejects_invalid_extension(self):
        response = self.post(self.docx("documento.txt"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(".docx", response.data["error"])
        self.assertIn(".pdf", response.data["error"])

    def test_rejects_invalid_output_format(self):
        response = self.post(self.docx(), "xlsx")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("escolha", response.data["error"].lower())

    def test_rejects_pdf_to_html(self):
        response = self.post(self.pdf(), "html")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("só podem", response.data["error"])

    def test_rejects_file_larger_than_ten_megabytes(self):
        response = self.post(self.docx(content=b"x" * (10 * 1024 * 1024 + 1)))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("10 MB", response.data["error"])

    def test_converts_to_markdown(self):
        with self.configure_successful_conversion("# Documento"):
            response = self.post(self.docx("meu arquivo.docx"), "markdown")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["content"], "# Documento")
        self.assertTrue(response.data["download_url"].endswith("/output.md"))
        conversion = Conversion.objects.get()
        self.assertEqual(conversion.status, Conversion.Status.COMPLETED)
        self.assertTrue(conversion.output_file.endswith("output.md"))

    def test_converts_to_html(self):
        with self.configure_successful_conversion("<!doctype html><p>Documento</p>"):
            response = self.post(self.docx(), "html")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["output_format"], "html")
        self.assertTrue(response.data["download_url"].endswith("/output.html"))

    def test_converts_docx_to_pdf_without_text_preview(self):
        with self.configure_successful_conversion(""):
            response = self.post(self.docx(), "pdf")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["content"])
        self.assertTrue(response.data["download_url"].endswith("/output.pdf"))

    def test_converts_pdf_to_docx_and_preserves_input_extension(self):
        with self.configure_successful_conversion(""):
            response = self.post(self.pdf("contrato.pdf"), "docx")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["content"])
        self.assertTrue(response.data["download_url"].endswith("/output.docx"))
        conversion = Conversion.objects.get()
        stored_input = (
            Path(self.temp_dir.name) / "conversions" / str(conversion.id) / "input.pdf"
        )
        self.assertTrue(stored_input.is_file())

    @patch(
        "conversions.views.DocumentConverter.convert",
        side_effect=ConversionDependencyError(
            "O conversor necessário não está instalado."
        ),
    )
    def test_reports_missing_dependency(self, _convert):
        response = self.post(self.docx())
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("não está instalado", response.data["error"])
        self.assertEqual(Conversion.objects.get().status, Conversion.Status.FAILED)

    @patch(
        "conversions.views.DocumentConverter.convert",
        side_effect=DocumentConversionError("Não foi possível converter o documento."),
    )
    def test_reports_conversion_error(self, _convert):
        response = self.post(self.docx())
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertFalse(response.data["success"])
        self.assertEqual(Conversion.objects.get().status, Conversion.Status.FAILED)

    def test_download_of_missing_conversion_returns_404(self):
        url = reverse(
            "conversion-download",
            kwargs={"conversion_id": uuid.uuid4(), "filename": "output.md"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_path_traversal_is_rejected(self):
        conversion = Conversion.objects.create(
            original_name="documento.docx",
            output_format="markdown",
            output_file="../secret.txt",
            status=Conversion.Status.COMPLETED,
        )
        url = reverse(
            "conversion-download",
            kwargs={"conversion_id": conversion.id, "filename": "output.md"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_original_filename_is_not_used_for_storage(self):
        with self.configure_successful_conversion("safe"):
            response = self.post(self.docx("..\\relatorio.docx"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversion = Conversion.objects.get()
        stored_input = (
            Path(self.temp_dir.name) / "conversions" / str(conversion.id) / "input.docx"
        )
        self.assertTrue(stored_input.is_file())

    def test_cors_allows_local_angular_frontend(self):
        response = self.client.options(
            self.url,
            HTTP_ORIGIN="http://localhost:4200",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://localhost:4200",
        )
