# -*- coding: utf-8 -*-
"""
Models for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


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
            self.title.capitalize()
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
