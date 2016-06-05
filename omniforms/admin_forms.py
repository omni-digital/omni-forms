# -*- coding: utf-8 -*-
"""
Admin forms for the omniforms app
"""
from __future__ import unicode_literals
from django import forms


class OmniModelFormAddFieldForm(forms.Form):
    """
    Form for chosing a field to add to the omni form
    """
    model_field = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        """
        Custom init method
        Sets choices on the 'field' field
        """
        choices = kwargs.pop('model_fields')
        super(OmniModelFormAddFieldForm, self).__init__(*args, **kwargs)
        self.fields['model_field'].choices = choices
