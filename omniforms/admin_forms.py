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


class OmniModelFormCreateFieldForm(forms.ModelForm):
    """
    Model form for creating omni field instances
    """
    def clean_widget_class(self):
        """
        Cleans the widget_class data submitted to the form

        :return: python dotted path for widget_class
        """
        widget_class = self.cleaned_data.get('widget_class')
        if widget_class not in self._meta.model.FORM_WIDGETS:
            raise forms.ValidationError('{0} is not a permitted widget'.format(widget_class))
        return widget_class
