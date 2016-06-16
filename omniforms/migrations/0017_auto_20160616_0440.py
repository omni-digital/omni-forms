# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('omniforms', '0016_auto_20160615_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='omnidecimalfield',
            name='initial',
            field=models.DecimalField(null=True, max_digits=1000, decimal_places=100, blank=True),
        ),
    ]
