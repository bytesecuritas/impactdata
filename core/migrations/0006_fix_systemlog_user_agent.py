# Generated manually to fix SystemLog user_agent field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_generalparameter_rolepermission_referencevalue_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemlog',
            name='user_agent',
            field=models.TextField(blank=True, null=True, verbose_name='User Agent'),
        ),
    ] 