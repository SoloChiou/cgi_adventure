from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


TRAITS = (
    ("strength", 9),
    ("intellect", 8),
    ("piety", 8),
    ("vitality", 9),
    ("dexterity", 9),
    ("speed", 8),
    ("charisma", 8),
)


def rebuild_player_stats(apps, schema_editor):
    Player = apps.get_model("game", "Player")
    for player in Player.objects.select_related("job").iterator():
        job = player.job
        player.max_hp = max(1, 5 * player.level + player.vitality + 16 + job.max_hp_bonus)
        player.max_mp = max(1, 2 * player.level + (player.intellect + player.piety) // 2 + job.max_mp_bonus)
        player.atk = max(0, 2 * player.level + player.strength - 3 + job.atk_bonus)
        player.defense = max(0, player.level + player.vitality // 4 + job.defense_bonus)
        player.intelligence = max(0, 2 * player.level + player.intellect - 7 + job.intelligence_bonus)
        player.magic_defense = max(0, (player.piety + player.charisma) // 8 + job.magic_defense_bonus)
        player.agility = max(0, player.level + (player.speed + player.dexterity) // 4 + job.agility_bonus)
        player.critical = min(Decimal("0.500"), job.critical_bonus)
        player.hp = min(player.hp, player.max_hp)
        player.mp = min(player.mp, player.max_mp)
        player.save()


class Migration(migrations.Migration):
    dependencies = [("game", "0007_job_archetype")]

    operations = [
        *[
            migrations.AddField(
                model_name="player",
                name=name,
                field=models.PositiveSmallIntegerField(default=default, validators=[MinValueValidator(1), MaxValueValidator(99)]),
            )
            for name, default in TRAITS
        ],
        *[
            migrations.AddConstraint(
                model_name="player",
                constraint=models.CheckConstraint(check=models.Q(**{f"{name}__gte": 1, f"{name}__lte": 99}), name=f"player_{name}_range"),
            )
            for name, _ in TRAITS
        ],
        migrations.RunPython(rebuild_player_stats, migrations.RunPython.noop),
    ]
