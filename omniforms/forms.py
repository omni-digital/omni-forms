# -*- coding: utf-8 -*-
"""
Forms for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured


class OmniFormBaseForm(forms.Form):
    """
    Base form for generated omni forms
    """
    _handlers = None

    def handle(self):
        """
        Really simple form handle method

        :return:
        """
        if not self.is_bound:
            raise ImproperlyConfigured(
                '\'{0}\' handle method cannot be called for '
                'unbound forms'.format(self.__class__.__name__)
            )

        if self._handlers:
            for handler in self._handlers:
                handler.handle(self)


class OmniModelFormBaseForm(forms.ModelForm, OmniFormBaseForm):
    """
    Base form for generated omni forms
    """
    def save(self, commit=True):
        self.handle()


class EmailConfirmationHandlerBaseFormClass(forms.ModelForm):
    """
    Custom wagtail admin base form class for the EmailConfirmationHandler model
    We provide this custom form class to restrict the recipient_field queryset
    to include only those OmniEmailField instances that belong to the same form
    as the handler
    """
    def __init__(self, *args, **kwargs):
        """
        Custom constructor method. Changes the recipient_field queryset to include
        only those OmniEmailField instances which belong to the same form as the
        EmailConfirmationHandler instance that is being  created or updated

        :param args: Default positional args
        :param kwargs: Default keyword args
        """
        super(EmailConfirmationHandlerBaseFormClass, self).__init__(*args, **kwargs)
        if self.instance and self.instance.form:
            qs = self.fields['recipient_field'].queryset.filter(
                content_type=ContentType.objects.get_for_model(self.instance.form),
                object_id=self.instance.form.id
            )
            self.fields['recipient_field'].queryset = qs
