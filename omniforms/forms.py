# -*- coding: utf-8 -*-
"""
Forms for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
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
