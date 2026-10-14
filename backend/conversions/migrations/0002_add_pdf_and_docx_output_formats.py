from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("conversions", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="conversion",
            name="output_format",
            field=models.CharField(
                choices=[
                    ("markdown", "Markdown"),
                    ("html", "HTML"),
                    ("pdf", "PDF"),
                    ("docx", "DOCX"),
                ],
                max_length=16,
            ),
        ),
    ]
