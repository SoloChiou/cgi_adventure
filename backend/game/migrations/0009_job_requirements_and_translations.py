from django.core.validators import MaxValueValidator
from django.db import migrations, models


TRAITS = ("strength", "intellect", "piety", "vitality", "dexterity", "speed", "charisma")


class Migration(migrations.Migration):
    dependencies = [("game", "0008_player_traits")]

    operations = [
        migrations.AddField(model_name="job", name="name_en", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="job", name="allowed_weapon_types", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="skill", name="name_en", field=models.CharField(blank=True, max_length=100)),
        *[
            migrations.AddField(
                model_name="job",
                name=f"required_{trait}",
                field=models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(99)]),
            )
            for trait in TRAITS
        ],
        *[
            migrations.AddConstraint(
                model_name="job",
                constraint=models.CheckConstraint(check=models.Q(**{f"required_{trait}__lte": 99}), name=f"job_required_{trait}_valid"),
            )
            for trait in TRAITS
        ],
    ]
