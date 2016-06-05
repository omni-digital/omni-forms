# -*- coding: utf-8 -*-
"""
Tests the omniforms models
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
from omniforms.models import (
    OmniFormBase,
    OmniModelFormBase,
    OmniForm,
    OmniModelForm,
    OmniField,
    OmniCharField,
    OmniBooleanField,
    OmniDateField,
    OmniDateTimeField,
    OmniDecimalField,
    OmniEmailField,
    OmniFloatField,
    OmniIntegerField,
    OmniTimeField,
    OmniUrlField,
)
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
        self.omniform = OmniForm.objects.create(title='test model')

    def test_get_form_class_name(self):
        """
        The _get_form_class_name method should return an appropriate name for the form
        """
        self.assertEqual('OmniFormTestModel', self.omniform._get_form_class_name())

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


class OmniFieldTestCase(TestCase):
    """
    Tests the OmniField model
    """
    def test_name_field(self):
        """
        The model should have a name field
        """
        field = OmniField._meta.get_field('name')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_label_field(self):
        """
        The model should have a label field
        """
        field = OmniField._meta.get_field('label')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_help_text_field(self):
        """
        The model should have a help_text field
        """
        field = OmniField._meta.get_field('help_text')
        self.assertIsInstance(field, models.TextField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_required_field(self):
        """
        The model should have a required field
        """
        field = OmniField._meta.get_field('required')
        self.assertIsInstance(field, models.BooleanField)
        self.assertFalse(field.default)

    def test_widget_class_field(self):
        """
        The model should have a widget_class field
        """
        field = OmniField._meta.get_field('widget_class')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_content_type_field(self):
        """
        The model should have a content_type field
        """
        field = OmniField._meta.get_field('content_type')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.rel.to, ContentType)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_object_id_field(self):
        """
        The model should have a object_id field
        """
        field = OmniField._meta.get_field('object_id')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_form_field(self):
        """
        The model should have a form field
        """
        field = OmniField.form
        self.assertIsInstance(field, GenericForeignKey)

    def test_string_representation(self):
        """
        The forms label should be used as the string representation
        """
        instance = OmniField(label='Do you like cats?')
        self.assertEqual('{0}'.format(instance), instance.label)

    def test_is_abstract(self):
        """
        The model class should be abstract
        """
        self.assertTrue(OmniField._meta.abstract)

    def test_get_concrete_class_for_model_field(self):
        """
        The get_concrete_class_for_model_field method should return the correct OmniField subclass
        """
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.CharField()), OmniCharField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.BooleanField()), OmniBooleanField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DateTimeField()), OmniDateTimeField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DecimalField()), OmniDecimalField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.EmailField()), OmniEmailField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.FloatField()), OmniFloatField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.IntegerField()), OmniIntegerField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.TimeField()), OmniTimeField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.URLField()), OmniUrlField)


class OmniCharFieldTestCase(TestCase):
    """
    Tests the OmniCharField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniCharField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniCharField._meta.get_field('initial')
        self.assertIsInstance(field, models.TextField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniBooleanFieldTestCase(TestCase):
    """
    Tests the OmniBooleanField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniBooleanField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniBooleanField._meta.get_field('initial')
        self.assertIsInstance(field, models.NullBooleanField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniEmailFieldTestCase(TestCase):
    """
    Tests the OmniEmailField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniEmailField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniEmailField._meta.get_field('initial')
        self.assertIsInstance(field, models.EmailField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniDateFieldTestCase(TestCase):
    """
    Tests the OmniDateField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniDateField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniDateField._meta.get_field('initial')
        self.assertIsInstance(field, models.DateField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniDateTimeFieldTestCase(TestCase):
    """
    Tests the OmniDateTimeField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniDateTimeField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniDateTimeField._meta.get_field('initial')
        self.assertIsInstance(field, models.DateTimeField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniDecimalFieldTestCase(TestCase):
    """
    Tests the OmniDecimalField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniDecimalField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniDecimalField._meta.get_field('initial')
        self.assertIsInstance(field, models.DecimalField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)
        self.assertEqual(field.decimal_places, 2)
        self.assertEqual(field.max_digits, 10)


class OmniFloatFieldTestCase(TestCase):
    """
    Tests the OmniFloatField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniFloatField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniFloatField._meta.get_field('initial')
        self.assertIsInstance(field, models.FloatField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniIntegerFieldTestCase(TestCase):
    """
    Tests the OmniIntegerField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniIntegerField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniIntegerField._meta.get_field('initial')
        self.assertIsInstance(field, models.IntegerField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniTimeFieldTestCase(TestCase):
    """
    Tests the OmniTimeField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniTimeField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniTimeField._meta.get_field('initial')
        self.assertIsInstance(field, models.TimeField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)


class OmniUrlFieldTestCase(TestCase):
    """
    Tests the OmniUrlField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniUrlField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniUrlField._meta.get_field('initial')
        self.assertIsInstance(field, models.URLField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)
