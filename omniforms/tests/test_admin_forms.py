# -*- coding: utf-8 -*-
"""
Tests the omniforms admin forms
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from omniforms.admin_forms import AddRelatedForm, OmniModelFormAdminForm
from omniforms.models import OmniModelForm
from omniforms.tests.models import DummyModel


class OmniModelFormAddFieldFormTestCase(TestCase):
    """
    Tests the OmniModelFormAddFieldForm form
    """
    def test_is_form(self):
        """
        The form class should extend django.forms.Form
        """
        self.assertTrue(issubclass(AddRelatedForm, forms.Form))

    def test_model_field(self):
        """
        The form should have a choices field
        """
        field = AddRelatedForm(choices=[]).fields['choices']
        self.assertIsInstance(field, forms.ChoiceField)

    def test_model_field_choices(self):
        """
        The forms choices field should take the choices from the kwargs on instanciation
        """
        choices = [('a', 'A'), ('b', 'B'), ('c', 'C')]
        field = AddRelatedForm(choices=choices).fields['choices']
        self.assertEqual(field.choices, choices)


class OmniModelFormAdminFormTestCase(TestCase):
    """
    Tests the OmniModelFormAdminForm
    """
    def test_is_form(self):
        """
        The form class should extend django.forms.ModelForm
        """
        self.assertTrue(issubclass(OmniModelFormAdminForm, forms.ModelForm))

    def test_uses_model(self):
        """
        The form class should use the correct model
        """
        self.assertEqual(OmniModelFormAdminForm._meta.model, OmniModelForm)

    @override_settings(OMNI_FORMS_EXCLUDED_CONTENT_TYPES=[{'app_label': 'tests'}])
    def test_permitted_content_types(self):
        """
        The forms content_type queryset should only include permitted content types
        """
        dummy_model_content_type = ContentType.objects.get_for_model(DummyModel)
        form = OmniModelFormAdminForm()
        self.assertNotIn(dummy_model_content_type, form.fields['content_type'].queryset)

    @override_settings(OMNI_FORMS_EXCLUDED_CONTENT_TYPES=[{'app_label': 'tests', 'model': 'dummymodel'}])
    def test_permitted_content_types_with_model(self):
        """
        The forms content_type queryset should only include permitted content types
        """
        dummy_model_content_type = ContentType.objects.get_for_model(DummyModel)
        form = OmniModelFormAdminForm()
        self.assertNotIn(dummy_model_content_type, form.fields['content_type'].queryset)

    def test_permitted_content_types_default(self):
        """
        The forms content_type queryset should exclude omniforms content types by default
        """
        form = OmniModelFormAdminForm()
        self.assertEqual(form.fields['content_type'].queryset.filter(app_label='omniforms').count(), 0)

    @override_settings(OMNI_FORMS_CONTENT_TYPES=[{'app_label': 'tests', 'model': 'dummymodel'}])
    def test_get_permitted_content_types_explicit_include(self):
        """
        The get_permitted_content_types method should only include specifically included models
        """
        dummy_model_content_type = ContentType.objects.get_for_model(DummyModel)
        form = OmniModelFormAdminForm()
        self.assertEqual(1, form.fields['content_type'].queryset.count())
        self.assertIn(dummy_model_content_type, form.fields['content_type'].queryset)
