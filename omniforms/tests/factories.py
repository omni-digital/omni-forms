# -*- coding: utf-8 -*-
"""
Factories for omniforms models
"""
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
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


class DummyModelFactory(factory.DjangoModelFactory):
    """
    Factory for creating dummy model instances
    """
    title = factory.Sequence(lambda n: 'Dummy Model {0}'.format(n))
    agree = True
    some_datetime = timezone.now()
    some_decimal = 0.67
    some_email = factory.Sequence(lambda n: 'test-{0}@example.com'.format(n))
    some_float = 3.945
    some_integer = factory.Sequence(lambda n: n)
    some_time = timezone.now().time()
    some_url = 'http://www.google.com'

    class Meta(object):
        """
        Factory meta
        """
        model = DummyModel
