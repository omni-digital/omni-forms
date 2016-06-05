# -*- coding: utf-8 -*-
"""
Tests the omniforms admin forms
"""
from __future__ import unicode_literals
from django import forms
from django.test import TestCase
from omniforms.admin_forms import OmniModelFormAddFieldForm
from omniforms.tests.factories import OmniModelFormFactory


class OmniModelFormAddFieldFormTestCase(TestCase):
    """
    Tests the OmniModelFormAddFieldForm form
    """
    def setUp(self):
        super(OmniModelFormAddFieldFormTestCase, self).setUp()
        self.form = OmniModelFormFactory.create()

    def test_is_form(self):
        """
        The form class should extend django.forms.Form
        """
        self.assertTrue(issubclass(OmniModelFormAddFieldForm, forms.Form))

    def test_model_field(self):
        """
        The form should have a model_field field
        """
        field = OmniModelFormAddFieldForm(model_fields=[]).fields['model_field']
        self.assertIsInstance(field, forms.ChoiceField)

    def test_model_field_choices(self):
        """
        The forms model_field field should take the choices from the kwargs on instanciation
        """
        model_fields = [('a', 'A'), ('b', 'B'), ('c', 'C')]
        field = OmniModelFormAddFieldForm(model_fields=model_fields).fields['model_field']
        self.assertEqual(field.choices, model_fields)
