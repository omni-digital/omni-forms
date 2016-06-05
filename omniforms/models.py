# -*- coding: utf-8 -*-
"""
Models for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
import re


@python_2_unicode_compatible
class OmniField(models.Model):
    """
    Base class for omni fields
    """
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    help_text = models.TextField(blank=True, null=True)
    required = models.BooleanField(default=False)
    widget_class = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    form = GenericForeignKey()

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    def __str__(self):
        """
        String representation of the instance

        :return: Fields label
        """
        return self.label

    @classmethod
    def get_concrete_class_for_model_field(cls, model_field):
        """
        Method for getting a concrete model class to represent the type of form field required

        :param model_field: Model Field instance
        :type model_field: django.forms.Field

        :return: OmniField subclass
        """
        return {
            models.CharField: OmniCharField,
            models.BooleanField: OmniBooleanField,
            models.DateField: OmniDateField,
            models.DateTimeField: OmniDateTimeField,
            models.DecimalField: OmniDecimalField,
            models.EmailField: OmniEmailField,
            models.FloatField: OmniFloatField,
            models.IntegerField: OmniIntegerField,
            models.TimeField: OmniTimeField,
            models.URLField: OmniUrlField
        }.get(model_field.__class__)


class OmniCharField(OmniField):
    """
    CharField representation
    """
    initial = models.TextField(blank=True, null=True)


class OmniBooleanField(OmniField):
    """
    BooleanField representation
    """
    initial = models.NullBooleanField()


class OmniDateField(OmniField):
    """
    DateField representation
    """
    initial = models.DateField(blank=True, null=True)


class OmniDateTimeField(OmniField):
    """
    DateTimeField representation
    """
    initial = models.DateTimeField(blank=True, null=True)


class OmniDecimalField(OmniField):
    """
    DecimalField representation
    """
    initial = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)


class OmniEmailField(OmniField):
    """
    EmailField representation
    """
    initial = models.EmailField(blank=True, null=True)


class OmniFloatField(OmniField):
    """
    FloatField representation
    """
    initial = models.FloatField(blank=True, null=True)


class OmniIntegerField(OmniField):
    """
    IntegerField representation
    """
    initial = models.IntegerField(blank=True, null=True)


class OmniTimeField(OmniField):
    """
    TimeField representation
    """
    initial = models.TimeField(blank=True, null=True)


class OmniUrlField(OmniField):
    """
    IntegerField representation
    """
    initial = models.URLField(blank=True, null=True)


@python_2_unicode_compatible
class OmniFormBase(models.Model):
    """
    Base class for the OmniForm model
    """
    title = models.CharField(max_length=255)

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    def __str__(self):
        """
        Method for generating a string representation of the instance

        :return: String representation of the instance
        """
        return self.title

    def _get_form_class_name(self):
        """
        Method for generating a name for the form class

        :return: Name for the form class
        """
        return str('{0}{1}'.format(
            self.__class__.__name__,
            ''.join([fragment.capitalize() for fragment in re.split('\W+', self.title)])
        ))

    @staticmethod
    def _get_form_class_bases():
        """
        Method for getting a tuple of base classes for the form

        :return: Tuple of base classes for the form
        """
        return forms.Form,

    def _get_form_class_properties(self):
        """
        Method for getting a dict of form properties

        :return: Dict of properties to set on the form class
        """
        return {'base_fields': []}

    def get_form_class(self):
        """
        Method for generating a form class from the data contained within the model

        :return: ModelForm class
        """
        return type(
            self._get_form_class_name(),
            self._get_form_class_bases(),
            self._get_form_class_properties()
        )


class OmniModelFormBase(OmniFormBase):
    """
    Base class for the OmniModelForm model
    """
    content_type = models.ForeignKey(ContentType, related_name='+')

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    @staticmethod
    def _get_form_class_bases():
        """
        Method for getting a tuple of base classes for the form

        :return: Tuple of base classes for the form
        """
        return forms.ModelForm,

    def _get_form_meta_class(self):
        """
        Method for getting a meta class for the form

        :return: Tuple of base classes for the form
        """
        model_class = self.content_type.model_class()
        return type(str('Meta'), (object,), {'model': model_class, 'fields': ()})

    def _get_form_class_properties(self):
        """
        Method for getting a dict of form properties

        :return: Dict of properties to set on the form class
        """
        return {
            'base_fields': [],
            'Meta': self._get_form_meta_class()
        }


class OmniForm(OmniFormBase):
    """
    Concrete implementation of the omni form
    """


class OmniModelForm(OmniModelFormBase):
    """
    Concrete implementation of the omni model form
    """
