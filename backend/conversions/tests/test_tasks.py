import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from conversions.models import Conversion
from conversions.services import DocumentConversionError
from conversions.tasks import cleanup_expired_conversions, process_conversion


class ConversionTaskTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=Path(self.temp_dir.name))
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.temp_dir.cleanup()

    def create_conversion(self, **changes):
        values = {
            "original_name": "documento.docx",
            "input_format": "docx",
            "input_file": "",
            "output_format": "pdf",
            "expires_at": timezone.now() + timedelta(hours=1),
        }
        values.update(changes)
        conversion = Conversion.objects.create(**values)
        directory = Path(self.temp_dir.name) / "conversions" / str(conversion.id)
        directory.mkdir(parents=True)
        input_path = directory / f"input.{conversion.input_format}"
        input_path.write_bytes(b"input")
        conversion.input_file = str(input_path.relative_to(self.temp_dir.name))
        conversion.save(update_fields=["input_file"])
        return conversion

    @patch("conversions.tasks.DocumentConverter.convert")
    def test_processes_conversion_successfully(self, convert):
        conversion = self.create_conversion()

        def create_output(_input, _format, directory):
            output = directory / "output.pdf"
            output.write_bytes(b"pdf")
            return output

        convert.side_effect = create_output
        result = process_conversion(str(conversion.id))

        conversion.refresh_from_db()
        self.assertEqual(result["status"], Conversion.Status.COMPLETED)
        self.assertEqual(conversion.status, Conversion.Status.COMPLETED)
        self.assertTrue(conversion.output_file.endswith("output.pdf"))
        self.assertIsNotNone(conversion.started_at)
        self.assertIsNotNone(conversion.completed_at)

    @patch("conversions.tasks.DocumentConverter.convert")
    def test_completed_task_is_idempotent(self, convert):
        conversion = self.create_conversion(status=Conversion.Status.COMPLETED)
        result = process_conversion(str(conversion.id))
        self.assertEqual(result["status"], Conversion.Status.COMPLETED)
        convert.assert_not_called()

    @patch(
        "conversions.tasks.DocumentConverter.convert",
        side_effect=DocumentConversionError("Documento inválido."),
    )
    def test_records_conversion_failure(self, _convert):
        conversion = self.create_conversion()
        result = process_conversion(str(conversion.id))
        conversion.refresh_from_db()
        self.assertEqual(result["status"], Conversion.Status.FAILED)
        self.assertEqual(conversion.status, Conversion.Status.FAILED)
        self.assertEqual(conversion.error_message, "Documento inválido.")

    @patch("conversions.tasks.DocumentConverter.convert")
    def test_stops_after_three_started_attempts(self, convert):
        conversion = self.create_conversion(attempt_count=3)
        result = process_conversion(str(conversion.id))
        conversion.refresh_from_db()
        self.assertEqual(result["status"], Conversion.Status.FAILED)
        self.assertIn("máximo de tentativas", conversion.error_message)
        convert.assert_not_called()

    @patch("conversions.tasks.DocumentConverter.convert")
    def test_worker_error_uses_conversion_language(self, convert):
        conversion = self.create_conversion(language="es-419", attempt_count=3)
        result = process_conversion(str(conversion.id))

        conversion.refresh_from_db()
        self.assertEqual(result["status"], Conversion.Status.FAILED)
        self.assertEqual(
            conversion.error_message,
            "La conversión superó el número máximo de intentos.",
        )
        convert.assert_not_called()

    def test_missing_input_is_reported(self):
        conversion = self.create_conversion()
        (Path(self.temp_dir.name) / conversion.input_file).unlink()
        result = process_conversion(str(conversion.id))
        conversion.refresh_from_db()
        self.assertEqual(result["status"], Conversion.Status.FAILED)
        self.assertIn("não foi encontrado", conversion.error_message)

    def test_cleanup_removes_expired_files(self):
        conversion = self.create_conversion(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        directory = Path(self.temp_dir.name) / "conversions" / str(conversion.id)

        result = cleanup_expired_conversions()

        conversion.refresh_from_db()
        self.assertEqual(result["removed"], 1)
        self.assertEqual(conversion.status, Conversion.Status.EXPIRED)
        self.assertFalse(directory.exists())

    def test_cleanup_does_not_remove_processing_conversion(self):
        conversion = self.create_conversion(
            status=Conversion.Status.PROCESSING,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        result = cleanup_expired_conversions()
        conversion.refresh_from_db()
        self.assertEqual(result["removed"], 0)
        self.assertEqual(conversion.status, Conversion.Status.PROCESSING)
