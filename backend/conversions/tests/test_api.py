import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from kombu.exceptions import OperationalError

from conversions.models import Conversion


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
    def docx(name="documento.docx", content=b"PK\x03\x04docx-content"):
        return SimpleUploadedFile(
            name,
            content,
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )

    @staticmethod
    def pdf(name="documento.pdf", content=b"%PDF-1.7"):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    def post(self, file=None, output_format="markdown"):
        data = {"output_format": output_format}
        if file is not None:
            data["file"] = file
        return self.client.post(self.url, data, format="multipart")

    def create_conversion(self, **changes):
        values = {
            "original_name": "documento.docx",
            "input_format": "docx",
            "input_file": "conversions/input.docx",
            "output_format": "markdown",
        }
        values.update(changes)
        return Conversion.objects.create(**values)

    def test_upload_without_file(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_rejects_invalid_extension(self):
        response = self.post(self.docx("documento.txt"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(".docx", response.data["error"])

    def test_rejects_pdf_to_html(self):
        response = self.post(self.pdf(), "html")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("só podem", response.data["error"])

    def test_rejects_file_larger_than_ten_megabytes(self):
        response = self.post(self.docx(content=b"x" * (10 * 1024 * 1024 + 1)))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("10 MB", response.data["error"])

    @patch("conversions.views.process_conversion.delay")
    def test_enqueues_conversion_and_returns_accepted(self, delay):
        response = self.post(self.docx("meu arquivo.docx"), "pdf")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["status"], Conversion.Status.PENDING)
        self.assertIn("status_url", response.data)
        conversion = Conversion.objects.get()
        delay.assert_called_once_with(str(conversion.id))
        self.assertEqual(conversion.input_format, "docx")
        self.assertTrue(conversion.input_file.endswith("input.docx"))
        self.assertTrue((Path(self.temp_dir.name) / conversion.input_file).is_file())

    @patch("conversions.views.process_conversion.delay")
    def test_pdf_input_preserves_extension(self, delay):
        response = self.post(self.pdf("contrato.pdf"), "docx")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        conversion = Conversion.objects.get()
        self.assertEqual(conversion.input_format, "pdf")
        self.assertTrue(conversion.input_file.endswith("input.pdf"))
        delay.assert_called_once()

    @patch(
        "conversions.views.process_conversion.delay",
        side_effect=OperationalError("redis unavailable"),
    )
    def test_reports_queue_unavailable(self, _delay):
        response = self.post(self.docx(), "pdf")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        conversion = Conversion.objects.get()
        self.assertEqual(conversion.status, Conversion.Status.FAILED)

    def test_returns_pending_conversion_status(self):
        conversion = self.create_conversion()
        response = self.client.get(
            reverse("conversion-detail", kwargs={"conversion_id": conversion.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Conversion.Status.PENDING)
        self.assertIsNone(response.data["download_url"])

    def test_returns_completed_conversion_with_download(self):
        conversion = self.create_conversion(
            output_file="",
            output_format="markdown",
            status=Conversion.Status.COMPLETED,
        )
        directory = Path(self.temp_dir.name) / "conversions" / str(conversion.id)
        directory.mkdir(parents=True)
        output = directory / "output.md"
        output.write_text("# Documento", encoding="utf-8")
        conversion.output_file = str(output.relative_to(self.temp_dir.name))
        conversion.save(update_fields=["output_file"])

        response = self.client.get(
            reverse("conversion-detail", kwargs={"conversion_id": conversion.id})
        )
        self.assertEqual(response.data["content"], "# Documento")
        self.assertTrue(response.data["download_url"].endswith("/output.md"))

    def test_download_before_completion_returns_404(self):
        conversion = self.create_conversion()
        url = reverse(
            "conversion-download",
            kwargs={"conversion_id": conversion.id, "filename": "output.md"},
        )
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_download_of_missing_conversion_returns_404(self):
        url = reverse(
            "conversion-download",
            kwargs={"conversion_id": uuid.uuid4(), "filename": "output.md"},
        )
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_path_traversal_is_rejected(self):
        conversion = self.create_conversion(
            output_file="../secret.txt",
            status=Conversion.Status.COMPLETED,
        )
        url = reverse(
            "conversion-download",
            kwargs={"conversion_id": conversion.id, "filename": "output.md"},
        )
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

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
