from django.db import migrations


CANCELLED_AREA_NAMES = ("蘭若古道", "等級模擬場")


def disable_cancelled_areas(apps, schema_editor):
    Area = apps.get_model("game", "Area")
    Area.objects.filter(name__in=CANCELLED_AREA_NAMES).update(enabled=False)


class Migration(migrations.Migration):
    dependencies = [("game", "0010_jobtitle_jobtitle_unique_job_title_rank_and_more")]

    operations = [migrations.RunPython(disable_cancelled_areas, migrations.RunPython.noop)]
