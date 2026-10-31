import shutil
from datetime import timedelta
from pathlib import Path

from celery.exceptions import CeleryError
from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from kombu.exceptions import OperationalError as QueueOperationalError

from .models import Conversion
from .serializers import ConversionRequestSerializer
from .tasks import process_conversion


TEXT_OUTPUT_FORMATS = {"markdown", "html"}
DOWNLOAD_FILENAMES = {"output.md", "output.html", "output.pdf", "output.docx"}


def first_validation_error(errors) -> str:
    for field_errors in errors.values():
        if isinstance(field_errors, dict):
            return first_validation_error(field_errors)
        if isinstance(field_errors, (list, tuple)) and field_errors:
            return str(field_errors[0])
        return str(field_errors)
    return "Dados inválidos."


def conversion_payload(conversion: Conversion, request=None) -> dict:
    payload = {
        "success": conversion.status not in {
            Conversion.Status.FAILED,
            Conversion.Status.EXPIRED,
        },
        "conversion_id": str(conversion.id),
        "original_name": conversion.original_name,
        "input_format": conversion.input_format,
        "output_format": conversion.output_format,
        "status": conversion.status,
        "error": (
            conversion.error_message
            if conversion.status == Conversion.Status.FAILED
            else ""
        ),
        "download_url": None,
        "content": None,
        "expires_at": conversion.expires_at,
    }
    if conversion.status != Conversion.Status.COMPLETED or not conversion.output_file:
        return payload

    output_path = (settings.MEDIA_ROOT / conversion.output_file).resolve()
    expected_dir = (
        settings.MEDIA_ROOT / "conversions" / str(conversion.id)
    ).resolve()
    if output_path.parent != expected_dir or not output_path.is_file():
        return payload

    url = reverse(
        "conversion-download",
        kwargs={"conversion_id": conversion.id, "filename": output_path.name},
    )
    payload["download_url"] = request.build_absolute_uri(url) if request else url
    if conversion.output_format in TEXT_OUTPUT_FORMATS:
        payload["content"] = output_path.read_text(encoding="utf-8")
    return payload


class ConversionCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ConversionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": first_validation_error(serializer.errors)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_file = serializer.validated_data["file"]
        output_format = serializer.validated_data["output_format"]
        input_extension = Path(uploaded_file.name).suffix.lower()
        retention = timedelta(minutes=settings.CONVERSION_RETENTION_MINUTES)
        conversion = Conversion.objects.create(
            original_name=Path(uploaded_file.name).name,
            input_format=input_extension.lstrip("."),
            input_file="",
            output_format=output_format,
            expires_at=timezone.now() + retention,
        )
        conversion_dir = settings.MEDIA_ROOT / "conversions" / str(conversion.id)
        input_path = conversion_dir / f"input{input_extension}"

        try:
            conversion_dir.mkdir(parents=True, exist_ok=False)
            with input_path.open("wb") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            conversion.input_file = str(input_path.relative_to(settings.MEDIA_ROOT))
            conversion.save(update_fields=["input_file"])
            process_conversion.delay(str(conversion.id))
        except (CeleryError, QueueOperationalError, OSError):
            shutil.rmtree(conversion_dir, ignore_errors=True)
            conversion.status = Conversion.Status.FAILED
            conversion.error_message = (
                "O serviço de conversão está temporariamente indisponível."
            )
            conversion.completed_at = timezone.now()
            conversion.save(
                update_fields=["status", "error_message", "completed_at"]
            )
            return Response(
                {"success": False, "error": conversion.error_message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = conversion_payload(conversion, request)
        payload["status_url"] = request.build_absolute_uri(
            reverse("conversion-detail", kwargs={"conversion_id": conversion.id})
        )
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class ConversionDetailView(APIView):
    def get(self, request, conversion_id):
        try:
            conversion = Conversion.objects.get(id=conversion_id)
        except Conversion.DoesNotExist as exc:
            raise Http404 from exc
        return Response(conversion_payload(conversion, request))


class ConversionDownloadView(APIView):
    def get(self, request, conversion_id, filename):
        if filename not in DOWNLOAD_FILENAMES:
            raise Http404

        try:
            conversion = Conversion.objects.get(
                id=conversion_id, status=Conversion.Status.COMPLETED
            )
        except Conversion.DoesNotExist as exc:
            raise Http404 from exc

        stored_path = (settings.MEDIA_ROOT / conversion.output_file).resolve()
        expected_dir = (
            settings.MEDIA_ROOT / "conversions" / str(conversion.id)
        ).resolve()
        if (
            stored_path.parent != expected_dir
            or stored_path.name != filename
            or not stored_path.is_file()
        ):
            raise Http404

        download_name = f"{Path(conversion.original_name).stem}{stored_path.suffix}"
        return FileResponse(
            stored_path.open("rb"), as_attachment=True, filename=download_name
        )
