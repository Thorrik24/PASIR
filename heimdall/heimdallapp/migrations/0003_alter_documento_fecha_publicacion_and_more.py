# Generated by Django 5.0.6 on 2024-06-17 17:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('heimdallapp', '0002_alter_documento_fecha_publicacion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documento',
            name='fecha_publicacion',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 17, 19, 52, 57, 803751)),
        ),
        migrations.AlterField(
            model_name='historial',
            name='fecha_operacion',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 17, 19, 52, 57, 803326)),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='fecha',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 17, 19, 52, 57, 802316)),
        ),
    ]
