from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("game", "0011_disable_cancelled_areas")]

    operations = [
        migrations.AddField(
            model_name="monster",
            name="name_en",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
