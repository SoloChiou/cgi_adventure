from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0013_area_encounter_weight_mode_monster_reference_hp_range"),
    ]

    operations = [
        migrations.AddField(
            model_name="area",
            name="encounter_monster_hp_max",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="area",
            name="encounter_monster_hp_min",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
