from django.core.validators import MinValueValidator
from django.db import migrations, models


def assign_job_skill_priorities(apps, schema_editor):
    Skill = apps.get_model("game", "Skill")
    job_ids = Skill.objects.order_by().values_list("job_id", flat=True).distinct()
    for job_id in job_ids:
        skill_ids = Skill.objects.filter(job_id=job_id).order_by("id").values_list("id", flat=True)
        for priority, skill_id in enumerate(skill_ids, start=1):
            Skill.objects.filter(id=skill_id).update(priority=priority)


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0005_add_skills"),
    ]

    operations = [
        migrations.AddField(
            model_name="skill",
            name="priority",
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.RunPython(assign_job_skill_priorities, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="skill",
            name="priority",
            field=models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)]),
        ),
        migrations.AlterModelOptions(
            name="skill",
            options={"ordering": ["priority", "id"]},
        ),
        migrations.AddConstraint(
            model_name="skill",
            constraint=models.UniqueConstraint(fields=("job", "priority"), name="unique_job_skill_priority"),
        ),
        migrations.DeleteModel(name="PlayerSkill"),
    ]
