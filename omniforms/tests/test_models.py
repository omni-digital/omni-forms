# -*- coding: utf-8 -*-
"""
Tests the omniforms models
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
from omniforms.models import OmniFormBase, OmniModelFormBase, OmniForm, OmniModelForm
from omniforms.tests.models import DummyModel


class OmniFormBaseTestCase(TestCase):
    """
    Tests the OmniFormBase class
    """
    def test_title_field(self):
        """
        The model should have a title field
        """
        field = OmniFormBase._meta.get_field('title')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_string_representation(self):
        """
        The models title should be used as the string representation
        """
        instance = OmniFormBase(title='test')
        self.assertEqual('{0}'.format(instance), instance.title)

    def test_is_abstract(self):
        """
        The model should be abstract
        """
        self.assertTrue(OmniFormBase._meta.abstract)


class OmniModelFormBaseTestCase(TestCase):
    """
    Tests the OmniModelFormBase class
    """
    def test_is_abstract(self):
        """
        The model should be abstract
        """
        self.assertTrue(OmniModelFormBase._meta.abstract)

    def test_content_type_field(self):
        """
        The model should have a content_type field
        """
        field = OmniModelFormBase._meta.get_field('content_type')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.rel.to, ContentType)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)


class OmniFormTestCase(TestCase):
    """
    Tests the OmniForm model
    """
    def setUp(self):
        super(OmniFormTestCase, self).setUp()
        self.omniform = OmniForm.objects.create(title='test')

    def test_get_form_class_name(self):
        """
        The _get_form_class_name method should return an appropriate name for the form
        """
        self.assertEqual('OmniFormTest', self.omniform._get_form_class_name())

    def test_get_form_class_bases(self):
        """
        The _get_form_class_bases method should return a tuple containing the django.forms.Form class
        """
        bases = self.omniform._get_form_class_bases()
        self.assertIn(forms.Form, bases)
        self.assertEqual(len(bases), 1)

    def test_get_form_class_properties(self):
        """
        The _get_form_class_properties method should return a dict of properties for the form class
        """
        properties = self.omniform._get_form_class_properties()
        self.assertIn('base_fields', properties)

    def test_get_form_class(self):
        """
        The _get_form_class method should return a form class
        """
        form_class = self.omniform.get_form_class()
        self.assertTrue(issubclass(form_class, forms.Form))


class OmniModelFormTestCase(TestCase):
    """
    Tests the OmniModelForm model
    """
    def setUp(self):
        super(OmniModelFormTestCase, self).setUp()
        self.omniform = OmniModelForm.objects.create(
            title='test',
            content_type=ContentType.objects.get_for_model(DummyModel)
        )

    def test_get_form_class(self):
        """
        The get_form_class method should return a form class
        """
        form_class = self.omniform.get_form_class()
        self.assertTrue(issubclass(form_class, forms.ModelForm))

    def test_get_form_class_properties(self):
        """
        The _get_form_class_properties method should return appropriate properties for the form
        """
        properties = self.omniform._get_form_class_properties()
        self.assertIn('base_fields', properties)
        self.assertIn('Meta', properties)

    def test_get_form_meta_class(self):
        """
        The _get_form_meta_class method should return a meta class for the form
        """
        meta_class = self.omniform._get_form_meta_class()
        self.assertEqual(meta_class.__name__, 'Meta')
        self.assertEqual(meta_class.model, DummyModel)
