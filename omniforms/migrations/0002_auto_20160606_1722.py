# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('omniforms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OmniFormHandler',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('object_id', models.PositiveIntegerField()),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='OmniFormEmailHandler',
            fields=[
                ('omniformhandler_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniFormHandler')),
                ('recipients', models.TextField()),
                ('subject', models.TextField()),
                ('template', models.TextField()),
            ],
            bases=('omniforms.omniformhandler',),
        ),
        migrations.AddField(
            model_name='omniformhandler',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
    ]
