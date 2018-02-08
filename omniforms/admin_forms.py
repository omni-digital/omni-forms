# -*- coding: utf-8 -*-
"""
Admin forms for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query import Q
from omniforms.models import OmniModelForm
import json


class AddRelatedForm(forms.Form):
    """
    Form for chosing a field to add to the omni form
    """
    choices = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        """
        Custom init method
        Sets choices on the 'field' field
        """
        choices = kwargs.pop('choices')
        super(AddRelatedForm, self).__init__(*args, **kwargs)
        self.fields['choices'].choices = choices


class FieldForm(forms.ModelForm):
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


class OmniModelFormAdminForm(forms.ModelForm):
    """
    Model form for creating and updating OmniModelForm instances
    """
    class Meta(object):
        """
        Django properties
        """
        model = OmniModelForm
        exclude = ()

    def __init__(self, *args, **kwargs):
        """
        Custom init method
        Sets the permitted content types on the form for creating/editing OmniModelForm model instances

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniModelFormAdminForm, self).__init__(*args, **kwargs)
        if 'content_type' in self.fields:  # content_type could be a readonly field
            self.fields['content_type'].queryset = self.get_permitted_content_types()

    @staticmethod
    def _query_filters(the_dict):
        """
        Method for generating Query filters to use when querying the ContentType model
        Used to either remove certain types of content from the omni model forms or to
        explicitly define which apps/models may be associated with an omni model form

        :param the_dict: Dictionary to construct the filters from
        :type the_dict: {}

        :return: Dict of model filters
        """
        kwargs = {}
        try:
            kwargs['app_label'] = the_dict['app_label']
        except KeyError:
            raise ImproperlyConfigured(
                'Dictionary \'{0}\' must contain an '
                'app_label'.format(json.dumps(the_dict))
            )

        if 'model' in the_dict:
            kwargs['model'] = the_dict['model']

        return kwargs

    def get_permitted_content_types(self):
        """
        Method for getting a queryset of permitted content types for the model form

        :return: QuerySet of ContentTYpe model instances
        """
        content_types = getattr(settings, 'OMNI_FORMS_CONTENT_TYPES', None)
        exclusions = getattr(settings, 'OMNI_FORMS_EXCLUDED_CONTENT_TYPES', [{'app_label': 'omniforms'}])
        qs = ContentType.objects.all()

        if content_types:
            query = None
            for content_type in content_types:
                kwargs = self._query_filters(content_type)
                if query is None:
                    query = Q(**kwargs)
                else:
                    query = query | Q(**kwargs)
            qs = qs.filter(query)

        elif exclusions:
            for exclusion in exclusions:
                kwargs = self._query_filters(exclusion)
                qs = qs.exclude(**kwargs)

        return qs
