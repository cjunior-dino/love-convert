from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("conversions", "0002_add_pdf_and_docx_output_formats")]

    operations = [
        migrations.AddField(
            model_name="conversion",
            name="input_file",
            field=models.CharField(default="", max_length=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="conversion",
            name="input_format",
            field=models.CharField(default="docx", max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="conversion",
            name="started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conversion",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conversion",
            name="expires_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="conversion",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pendente"),
                    ("processing", "Processando"),
                    ("completed", "Concluída"),
                    ("failed", "Falhou"),
                    ("expired", "Expirada"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
    ]
