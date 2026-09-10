from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("game", "0006_automatic_job_skills")]

    operations = [
        migrations.AddField(
            model_name="job",
            name="archetype",
            field=models.CharField(choices=[("physical", "物理"), ("magical", "魔法")], default="physical", max_length=12),
        ),
    ]
