import uuid

from django.db import models


class Conversion(models.Model):
    class OutputFormat(models.TextChoices):
        MARKDOWN = "markdown", "Markdown"
        HTML = "html", "HTML"
        PDF = "pdf", "PDF"
        DOCX = "docx", "DOCX"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        COMPLETED = "completed", "Concluída"
        FAILED = "failed", "Falhou"
        EXPIRED = "expired", "Expirada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_name = models.CharField(max_length=255)
    input_format = models.CharField(max_length=16)
    input_file = models.CharField(max_length=500)
    output_format = models.CharField(max_length=16, choices=OutputFormat.choices)
    output_file = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True)
    language = models.CharField(max_length=10, default="pt-br")
    attempt_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
