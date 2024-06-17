# Generated by Django 5.0.6 on 2024-06-17 17:53

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('heimdallapp', '0003_alter_documento_fecha_publicacion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documento',
            name='fecha_publicacion',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 17, 19, 53, 4, 683921)),
        ),
        migrations.AlterField(
            model_name='historial',
            name='fecha_operacion',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 17, 19, 53, 4, 683530)),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='fecha',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 17, 19, 53, 4, 682787)),
        ),
    ]