# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='OmniField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('label', models.CharField(max_length=255)),
                ('help_text', models.TextField(null=True, blank=True)),
                ('required', models.BooleanField(default=False)),
                ('widget_class', models.CharField(max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('object_id', models.PositiveIntegerField()),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='OmniForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OmniModelForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('content_type', models.ForeignKey(related_name='+', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OmniBooleanField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.NullBooleanField()),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniCharField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.TextField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniDateField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.DateField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniDateTimeField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.DateTimeField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniDecimalField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.DecimalField(null=True, max_digits=10, decimal_places=2, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniEmailField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.EmailField(max_length=254, null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniFloatField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.FloatField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniIntegerField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.IntegerField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniTimeField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.TimeField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.CreateModel(
            name='OmniUrlField',
            fields=[
                ('omnifield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='omniforms.OmniField')),
                ('initial', models.URLField(null=True, blank=True)),
            ],
            bases=('omniforms.omnifield',),
        ),
        migrations.AddField(
            model_name='omnifield',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='omnifield',
            name='real_type',
            field=models.ForeignKey(related_name='+', to='contenttypes.ContentType'),
        ),
    ]
