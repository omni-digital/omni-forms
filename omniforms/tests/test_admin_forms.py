# -*- coding: utf-8 -*-
"""
Tests the omniforms admin forms
"""
from __future__ import unicode_literals
from django import forms
from django.test import TestCase
from omniforms.admin_forms import OmniModelFormAddRelatedForm


class OmniModelFormAddFieldFormTestCase(TestCase):
    """
    Tests the OmniModelFormAddFieldForm form
    """
    def test_is_form(self):
        """
        The form class should extend django.forms.Form
        """
        self.assertTrue(issubclass(OmniModelFormAddRelatedForm, forms.Form))

    def test_model_field(self):
        """
        The form should have a choices field
        """
        field = OmniModelFormAddRelatedForm(choices=[]).fields['choices']
        self.assertIsInstance(field, forms.ChoiceField)

    def test_model_field_choices(self):
        """
        The forms choices field should take the choices from the kwargs on instanciation
        """
        choices = [('a', 'A'), ('b', 'B'), ('c', 'C')]
        field = OmniModelFormAddRelatedForm(choices=choices).fields['choices']
        self.assertEqual(field.choices, choices)
