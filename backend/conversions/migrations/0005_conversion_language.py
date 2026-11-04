from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("conversions", "0004_conversion_attempt_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversion",
            name="language",
            field=models.CharField(default="pt-br", max_length=10),
        ),
    ]
