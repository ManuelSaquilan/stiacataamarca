# Generated by Django 4.2.3 on 2025-03-27 01:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordenes', '0007_alter_customuser_tipo_acceso'),
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=50, verbose_name='Nombre de la Empresa')),
                ('direccion', models.CharField(blank=True, max_length=100, null=True, verbose_name='Dirección')),
                ('telefono', models.CharField(blank=True, max_length=20, null=True, verbose_name='Teléfono')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'empresa',
                'verbose_name_plural': 'empresas',
                'db_table': 'empresa',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='empleado',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordenes.empresa', verbose_name='Empresa'),
        ),
    ]
