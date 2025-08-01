# Generated by Django 5.2.3 on 2025-07-06 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_merge_20250706_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interaction',
            name='identifiant',
            field=models.CharField(editable=False, max_length=20, unique=True, verbose_name='Identifiant'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='identifiant',
            field=models.IntegerField(editable=False, unique=True, verbose_name="Identifiant de l'organisation"),
        ),
    ]
