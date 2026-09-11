from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("game", "0014_area_encounter_monster_hp_bounds")]

    operations = [
        migrations.AddField(model_name="player", name="battle_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="player", name="victory_count", field=models.PositiveIntegerField(default=0)),
    ]
