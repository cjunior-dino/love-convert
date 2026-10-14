from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import reverse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversion
from .serializers import ConversionRequestSerializer
from .services import (
    ConversionDependencyError,
    DocumentConversionError,
    DocumentConverter,
)


TEXT_OUTPUT_FORMATS = {"markdown", "html"}
DOWNLOAD_FILENAMES = {"output.md", "output.html", "output.pdf", "output.docx"}


def first_validation_error(errors) -> str:
    for field_errors in errors.values():
        if isinstance(field_errors, (list, tuple)) and field_errors:
            return str(field_errors[0])
        return str(field_errors)
    return "Dados inválidos."


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
        conversion = Conversion.objects.create(
            original_name=Path(uploaded_file.name).name,
            output_format=output_format,
        )
        conversion_dir = settings.MEDIA_ROOT / "conversions" / str(conversion.id)
        conversion_dir.mkdir(parents=True, exist_ok=False)
        input_extension = Path(uploaded_file.name).suffix.lower()
        input_path = conversion_dir / f"input{input_extension}"

        try:
            with input_path.open("wb") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            conversion.status = Conversion.Status.PROCESSING
            conversion.save(update_fields=["status"])
            output_path = DocumentConverter().convert(
                input_path, output_format, conversion_dir
            )
            conversion.output_file = str(output_path.relative_to(settings.MEDIA_ROOT))
            conversion.status = Conversion.Status.COMPLETED
            conversion.error_message = ""
            conversion.save(
                update_fields=["output_file", "status", "error_message"]
            )

            content = (
                output_path.read_text(encoding="utf-8")
                if output_format in TEXT_OUTPUT_FORMATS
                else None
            )
            download_url = reverse(
                "conversion-download",
                kwargs={
                    "conversion_id": conversion.id,
                    "filename": output_path.name,
                },
            )
            return Response(
                {
                    "success": True,
                    "original_name": conversion.original_name,
                    "output_format": output_format,
                    "content": content,
                    "download_url": download_url,
                },
                status=status.HTTP_201_CREATED,
            )
        except (ConversionDependencyError, DocumentConversionError) as exc:
            conversion.status = Conversion.Status.FAILED
            conversion.error_message = str(exc)
            conversion.save(update_fields=["status", "error_message"])
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
                if isinstance(exc, ConversionDependencyError)
                else status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception:
            conversion.status = Conversion.Status.FAILED
            conversion.error_message = "Não foi possível converter o arquivo."
            conversion.save(update_fields=["status", "error_message"])
            return Response(
                {"success": False, "error": "Não foi possível converter o arquivo."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
