# Generated by Django 4.2.3 on 2025-03-25 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordenes', '0003_deuda'),
    ]

    operations = [
        migrations.AddField(
            model_name='deuda',
            name='activo',
            field=models.BooleanField(default=True, verbose_name='Activo'),
        ),
    ]
