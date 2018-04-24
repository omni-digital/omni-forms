# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-23 05:48
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    OmniManyToManyField = apps.get_model('omniforms', 'OmniManyToManyField')
    OmniManyToManyFieldNew = apps.get_model('omniforms', 'OmniManyToManyFieldNew')
    OmniForeignKeyField = apps.get_model('omniforms', 'OmniForeignKeyField')
    OmniForeignKeyFieldNew = apps.get_model('omniforms', 'OmniForeignKeyFieldNew')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    m2m_ctype = ContentType.objects.get_for_model(OmniManyToManyFieldNew)
    for instance in OmniManyToManyField.objects.all():
        name = instance.name
        instance.name = name + '_old'
        instance.save()

        OmniManyToManyFieldNew.objects.create(
            related_type_id=instance.related_type_id,
            name=name,
            label=instance.label,
            help_text=instance.help_text,
            required=instance.required,
            widget_class=instance.widget_class,
            order=instance.order,
            real_type=m2m_ctype,
            content_type=instance.content_type,
            object_id=instance.object_id
        )

    fk_ctype = ContentType.objects.get_for_model(OmniForeignKeyFieldNew)
    for instance in OmniForeignKeyField.objects.all():
        name = instance.name
        instance.name = name + '_old'
        instance.save()

        OmniForeignKeyFieldNew.objects.create(
            related_type_id=instance.related_type_id,
            name=name,
            label=instance.label,
            help_text=instance.help_text,
            required=instance.required,
            widget_class=instance.widget_class,
            order=instance.order,
            real_type=fk_ctype,
            content_type=instance.content_type,
            object_id=instance.object_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('omniforms', '0022_omniforeignkeyfieldnew_omnimanytomanyfieldnew'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
