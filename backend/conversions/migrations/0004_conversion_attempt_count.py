from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("conversions", "0003_async_conversion_fields")]

    operations = [
        migrations.AddField(
            model_name="conversion",
            name="attempt_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
