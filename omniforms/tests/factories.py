# -*- coding: utf-8 -*-
"""
Factories for omniforms models
"""
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from omniforms.models import OmniForm, OmniModelForm
from omniforms.tests.models import DummyModel
import factory


class OmniFormFactory(factory.DjangoModelFactory):
    """
    Factory for creating OmniForm model instances
    """
    title = factory.Sequence(lambda n: 'Omni Form {0}'.format(n))

    class Meta(object):
        """
        Factory meta
        """
        model = OmniForm


class OmniModelFormFactory(factory.DjangoModelFactory):
    """
    Factory for creating OmniModelForm model instances
    """
    title = factory.Sequence(lambda n: 'Omni Model Form {0}'.format(n))
    content_type = factory.LazyAttribute(lambda n: ContentType.objects.get_for_model(DummyModel))

    class Meta(object):
        """
        Factory meta
        """
        model = OmniModelForm
