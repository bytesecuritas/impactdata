import uuid
from django.db import migrations, models


def gen_uuid(apps, schema_editor):
    Organization = apps.get_model('core', 'Organization')
    for org in Organization.objects.all():
        if not org.registration_token:
            org.registration_token = uuid.uuid4()
            org.save(update_fields=['registration_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_registration_request_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='registration_token',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, null=True, verbose_name="Jeton d'inscription publique"),
        ),
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='organization',
            name='registration_token',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="Jeton d'inscription publique"),
        ),
    ]
