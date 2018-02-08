# -*- coding: utf-8 -*-
"""
Factories for omniforms models
"""
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from omniforms.models import OmniForm, OmniModelForm, OmniFormEmailHandler, OmniCharField
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


class OmniFormEmailHandlerFactory(factory.DjangoModelFactory):
    """
    Model factory for creating OmniFormEmailHandler instances
    """
    subject = factory.Sequence(lambda n: 'Email Handler {0}'.format(n))
    recipients = factory.Sequence(lambda n: 'foo{0}@example.com,bar{0}@example.com'.format(n))
    template = factory.Sequence(lambda n: 'This is some test content {0}'.format(n))
    name = factory.Sequence(lambda n: 'Email Handler {0}'.format(n))
    order = factory.Sequence(lambda n: n)
    form = factory.SubFactory(OmniModelFormFactory)

    class Meta(object):
        """
        Factory meta
        """
        model = OmniFormEmailHandler


class OmniCharFieldFactory(factory.DjangoModelFactory):
    """
    Factory for creating OmniCharField instances
    """
    name = factory.Sequence('charfield_{0}'.format)
    label = factory.Sequence('CharField Label {0}'.format)
    widget_class = 'django.forms.widgets.TextInput'

    class Meta(object):
        """
        FactoryBoy properties
        """
        model = OmniCharField


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
