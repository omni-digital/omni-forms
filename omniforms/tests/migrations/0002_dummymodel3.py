# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-10 14:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyModel3',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.ManyToManyField(to='tests.DummyModel')),
            ],
        ),
    ]