# Generated manually to add is_system field to ReferenceValue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_fix_systemlog_user_agent'),
    ]

    operations = [
        migrations.AddField(
            model_name='referencevalue',
            name='is_system',
            field=models.BooleanField(default=False, verbose_name='Valeur système'),
        ),
    ] 