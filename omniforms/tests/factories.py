# -*- coding: utf-8 -*-
"""
Factories for omniforms models
"""
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from omniforms.models import (
    OmniForm,
    OmniModelForm,
    OmniFormEmailHandler,
    OmniFormEmailConfirmationHandler,
    OmniCharField,
    OmniBooleanField,
    OmniEmailField
)
from omniforms.tests.models import DummyModel
import factory


class UserFactory(factory.DjangoModelFactory):
    """
    Factory for generating user model instances
    """
    username = factory.Sequence('user{0}'.format)
    email = factory.Sequence('user{0}@example.com'.format)
    is_staff = False
    is_superuser = False
    is_active = True

    class Meta(object):
        """
        FactoryBoy properties
        """
        model = get_user_model()


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


class OmniFormEmailConfirmationHandlerFactory(factory.DjangoModelFactory):
    """
    Factory for creating OmniFormEmailConfirmationHandler instances
    """
    name = factory.Sequence('Email confirmation handler name {0}'.format)
    order = 0
    subject = factory.Sequence('Email confirmation handler subject {0}'.format)
    template = factory.Sequence('Email confirmation handler template {0}'.format)
    form = factory.SubFactory(OmniFormFactory)

    class Meta:
        """
        Factory boy properties.
        """
        model = OmniFormEmailConfirmationHandler


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


class OmniBooleanFieldFactory(factory.DjangoModelFactory):
    """
    Model factory for generating OmniBooleanField instances
    """
    name = factory.Sequence('boolean_field_{0}'.format)
    label = factory.Sequence('Boolean field {0}'.format)
    widget_class = 'django.forms.widgets.CheckboxInput'
    order = factory.Sequence(lambda n: n)
    form = factory.SubFactory(OmniFormFactory)

    class Meta(object):
        model = OmniBooleanField


class OmniEmailFieldFactory(factory.DjangoModelFactory):
    """
    Model factory for generating OmniEmailField instances
    """
    name = factory.Sequence('email_field_{0}'.format)
    label = factory.Sequence('Email field {0}'.format)
    widget_class = 'django.forms.widgets.EmailInput'
    order = factory.Sequence(lambda n: n)
    form = factory.SubFactory(OmniFormFactory)

    class Meta(object):
        model = OmniEmailField


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
