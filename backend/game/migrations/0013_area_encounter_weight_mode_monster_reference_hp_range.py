from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("game", "0012_monster_name_en")]

    operations = [
        migrations.AddField(
            model_name="area",
            name="encounter_weight_mode",
            field=models.CharField(
                choices=[("fixed", "固定權重"), ("reference_hp", "FF Adventure HP 權重")],
                default="fixed",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="monster",
            name="reference_hp_range",
            field=models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)]),
        ),
        migrations.AddConstraint(
            model_name="monster",
            constraint=models.CheckConstraint(
                check=models.Q(reference_hp_range__gte=1),
                name="monster_reference_hp_range_valid",
            ),
        ),
    ]
