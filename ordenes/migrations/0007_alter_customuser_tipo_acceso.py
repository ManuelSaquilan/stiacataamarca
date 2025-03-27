# Generated by Django 4.2.3 on 2025-03-26 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordenes', '0006_customuser_tipo_acceso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='tipo_acceso',
            field=models.CharField(blank=True, choices=[('tipo_1', 'Administrador Tipo full'), ('tipo_2', 'Administrador Tipo emite ordenes'), ('tipo_3', 'Administrador Tipo Comercio')], default='tipo_3', max_length=10, null=True, verbose_name='Tipo de Acceso'),
        ),
    ]
