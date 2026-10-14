import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Conversion",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("original_name", models.CharField(max_length=255)),
                (
                    "output_format",
                    models.CharField(
                        choices=[("markdown", "Markdown"), ("html", "HTML")],
                        max_length=16,
                    ),
                ),
                ("output_file", models.CharField(blank=True, max_length=500)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("processing", "Processando"),
                            ("completed", "Concluída"),
                            ("failed", "Falhou"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        )
    ]
