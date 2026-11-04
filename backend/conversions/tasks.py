import shutil

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Conversion
from .i18n import localized_exception_message, translate
from .services import (
    ConversionDependencyError,
    DocumentConversionError,
    DocumentConverter,
)


def _mark_failed(conversion_id: str, message: str) -> None:
    Conversion.objects.filter(id=conversion_id).update(
        status=Conversion.Status.FAILED,
        error_message=message,
        completed_at=timezone.now(),
    )


@shared_task(name="conversions.process_conversion", acks_late=True)
def process_conversion(conversion_id: str) -> dict[str, str]:
    with transaction.atomic():
        conversion = Conversion.objects.select_for_update().get(id=conversion_id)
        if conversion.status == Conversion.Status.COMPLETED:
            return {"status": Conversion.Status.COMPLETED}
        if conversion.status == Conversion.Status.EXPIRED:
            return {"status": Conversion.Status.EXPIRED}
        if conversion.attempt_count >= 3:
            conversion.status = Conversion.Status.FAILED
            conversion.error_message = translate(
                "task.max_attempts", conversion.language
            )
            conversion.completed_at = timezone.now()
            conversion.save(
                update_fields=["status", "error_message", "completed_at"]
            )
            return {"status": Conversion.Status.FAILED}
        conversion.status = Conversion.Status.PROCESSING
        conversion.started_at = timezone.now()
        conversion.error_message = ""
        conversion.attempt_count += 1
        conversion.save(
            update_fields=[
                "status",
                "started_at",
                "error_message",
                "attempt_count",
            ]
        )

    input_path = (settings.MEDIA_ROOT / conversion.input_file).resolve()
    conversion_dir = (
        settings.MEDIA_ROOT / "conversions" / str(conversion.id)
    ).resolve()
    media_root = settings.MEDIA_ROOT.resolve()

    if media_root not in input_path.parents or input_path.parent != conversion_dir:
        _mark_failed(
            conversion_id, translate("task.invalid_source", conversion.language)
        )
        return {"status": Conversion.Status.FAILED}
    if not input_path.is_file():
        _mark_failed(
            conversion_id, translate("task.missing_source", conversion.language)
        )
        return {"status": Conversion.Status.FAILED}

    try:
        output_path = DocumentConverter().convert(
            input_path, conversion.output_format, conversion_dir
        )
        relative_output = output_path.relative_to(settings.MEDIA_ROOT)
        Conversion.objects.filter(id=conversion_id).update(
            output_file=str(relative_output),
            status=Conversion.Status.COMPLETED,
            error_message="",
            completed_at=timezone.now(),
        )
        return {"status": Conversion.Status.COMPLETED}
    except (ConversionDependencyError, DocumentConversionError) as exc:
        _mark_failed(
            conversion_id, localized_exception_message(exc, conversion.language)
        )
        return {"status": Conversion.Status.FAILED}
    except Exception:
        _mark_failed(
            conversion_id, translate("task.generic_failure", conversion.language)
        )
        return {"status": Conversion.Status.FAILED}


@shared_task(name="conversions.cleanup_expired_conversions")
def cleanup_expired_conversions() -> dict[str, int]:
    now = timezone.now()
    expired = Conversion.objects.filter(expires_at__lte=now).exclude(
        status__in=[Conversion.Status.PROCESSING, Conversion.Status.EXPIRED]
    )
    removed = 0
    for conversion in expired.iterator():
        conversion_dir = settings.MEDIA_ROOT / "conversions" / str(conversion.id)
        shutil.rmtree(conversion_dir, ignore_errors=True)
        conversion.status = Conversion.Status.EXPIRED
        conversion.input_file = ""
        conversion.output_file = ""
        conversion.save(update_fields=["status", "input_file", "output_file"])
        removed += 1
    return {"removed": removed}
