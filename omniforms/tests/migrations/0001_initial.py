# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DummyModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('agree', models.BooleanField()),
                ('some_date', models.DateField()),
                ('some_datetime', models.DateTimeField()),
                ('some_decimal', models.DecimalField(max_digits=12, decimal_places=10)),
                ('some_email', models.EmailField(max_length=254)),
                ('some_float', models.FloatField()),
                ('some_integer', models.IntegerField()),
                ('some_time', models.TimeField()),
                ('some_url', models.URLField()),
            ],
        ),
    ]
