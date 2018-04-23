# -*- coding: utf-8 -*-
"""
Tests the omniforms models
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.module_loading import import_string
from mock import Mock, patch, PropertyMock
from omniforms.forms import OmniFormBaseForm, OmniModelFormBaseForm, EmailConfirmationHandlerBaseFormClass
from omniforms.models import (
    OmniFormBase,
    OmniModelFormBase,
    OmniForm,
    OmniField,
    OmniCharField,
    OmniBooleanField,
    OmniDurationField,
    OmniDateField,
    OmniDateTimeField,
    OmniDecimalField,
    OmniEmailField,
    OmniFileField,
    OmniFloatField,
    OmniGenericIPAddressField,
    OmniImageField,
    OmniIntegerField,
    OmniTimeField,
    OmniUrlField,
    OmniSlugField,
    OmniUUIDField,
    OmniManyToManyField,
    OmniForeignKeyField,
    OmniMultipleChoiceField,
    OmniChoiceField,
    OmniFormHandler,
    OmniFormEmailHandler,
    OmniFormEmailConfirmationHandler,
    OmniFormSaveInstanceHandler,
    TemplateHelpTextLazy
)
from omniforms.tests.factories import (
    DummyModelFactory,
    OmniFormFactory,
    OmniModelFormFactory,
    OmniEmailFieldFactory,
    OmniFormEmailConfirmationHandlerFactory,
    OmniFormEmailHandlerFactory
)
from omniforms.tests.models import TaggableManagerField, DummyModel2
from omniforms.tests.utils import OmniModelFormTestCaseStub
from taggit_autosuggest.managers import TaggableManager
from unittest import skipUnless

import django
import os


TEST_FILE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        instance = OmniFormBase()
        instance.title = 'test'
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


class OmniFormTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniForm model
    """
    def setUp(self):
        super(OmniFormTestCase, self).setUp()
        self.omniform = OmniForm.objects.create(title='test model')
        self.field_1 = OmniCharField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='Some title...',
            form=self.omniform
        )
        self.field_1.save()
        self.field_2 = OmniBooleanField(
            name='agree',
            label='Please agree',
            required=True,
            widget_class='django.forms.widgets.CheckboxInput',
            order=1,
            initial_data=True,
            form=self.omniform
        )
        self.field_2.save()
        self.handler_1 = OmniFormEmailHandlerFactory.create(form=self.omniform)
        self.handler_2 = OmniFormEmailHandlerFactory.create(form=self.omniform)

    def test_get_form_class_name(self):
        """
        The _get_form_class_name method should return an appropriate name for the form
        """
        self.assertEqual('OmniFormTestModel', self.omniform._get_form_class_name())

    def test_get_form_class(self):
        """
        The _get_form_class method should return a form class
        """
        form_class = self.omniform.get_form_class()
        self.assertTrue(issubclass(form_class, OmniFormBaseForm))
        self.assertEqual(form_class.__name__, 'OmniFormTestModel')
        form = form_class()

        # Test the title field
        self.assertIsInstance(form.fields['title'], forms.CharField)
        self.assertIsInstance(form.fields['title'].widget, forms.TextInput)
        self.assertEqual(form.fields['title'].label, 'Please give us a title')
        self.assertEqual(form.fields['title'].initial, 'Some title...')
        self.assertTrue(form.fields['title'].required)

        # Test the agree field
        self.assertIsInstance(form.fields['agree'], forms.BooleanField)
        self.assertIsInstance(form.fields['agree'].widget, forms.CheckboxInput)
        self.assertEqual(form.fields['agree'].label, 'Please agree')
        self.assertTrue(form.fields['agree'].initial)
        self.assertTrue(form.fields['agree'].required)

    def test_used_field_names(self):
        """
        The used_field_names property of the model should return names of fields used on the form
        """
        used_field_names = self.omniform.used_field_names
        self.assertEqual(len(used_field_names), 2)
        self.assertIn('title', used_field_names)
        self.assertIn('agree', used_field_names)

    def test_get_fields(self):
        """
        The method should return the correct fields as a dict
        """
        fields = self.omniform._get_fields()
        self.assertEqual(2, len(fields))

        # Test the title field
        self.assertIsInstance(fields['title'], forms.CharField)
        self.assertIsInstance(fields['title'].widget, forms.TextInput)
        self.assertEqual(fields['title'].label, 'Please give us a title')
        self.assertEqual(fields['title'].initial, 'Some title...')
        self.assertTrue(fields['title'].required)

        # Test the agree field
        self.assertIsInstance(fields['agree'], forms.BooleanField)
        self.assertIsInstance(fields['agree'].widget, forms.CheckboxInput)
        self.assertEqual(fields['agree'].label, 'Please agree')
        self.assertTrue(fields['agree'].initial)
        self.assertTrue(fields['agree'].required)


class OmniModelFormTestCase(TestCase):
    """
    Tests the OmniModelForm model
    """
    def setUp(self):
        super(OmniModelFormTestCase, self).setUp()
        self.omniform = OmniModelFormFactory.create()
        self.field_1 = OmniCharField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='Some title...',
            form=self.omniform
        )
        self.field_1.save()
        self.field_2 = OmniBooleanField(
            name='agree',
            label='Please agree',
            required=True,
            widget_class='django.forms.widgets.CheckboxInput',
            order=1,
            initial_data=True,
            form=self.omniform
        )
        self.field_2.save()
        self.handler_1 = OmniFormEmailHandlerFactory.create(form=self.omniform)
        self.handler_2 = OmniFormEmailHandlerFactory.create(form=self.omniform)

    def test_get_field(self):
        """
        The _get_field method should return a form field instance
        """
        field_1 = self.omniform._get_field('title')
        field_2 = self.omniform._get_field('agree')
        field_3 = self.omniform._get_field('fictional')
        self.assertIsInstance(field_1, forms.CharField)
        self.assertIsInstance(field_1.widget, forms.TextInput)
        self.assertEqual(field_1.label, 'Please give us a title')
        self.assertTrue(field_1.required)
        self.assertIsInstance(field_2, forms.BooleanField)
        self.assertIsInstance(field_2.widget, forms.CheckboxInput)
        self.assertEqual(field_2.label, 'Please agree')
        self.assertTrue(field_2.required)
        self.assertIsNone(field_3)

    def test_get_form_class(self):
        """
        The get_form_class method should return a form class
        """
        form_class = self.omniform.get_form_class()
        self.assertTrue(issubclass(form_class, OmniModelFormBaseForm))

    @patch('omniforms.models.OmniModelForm.used_field_names',
           PropertyMock(return_value=['foo', 'bar', 'baz']))
    @patch('omniforms.models.OmniModelForm._get_base_form_class')
    @patch('omniforms.models.modelform_factory')
    def test_get_form_class_calls_modelform_factory(self, modelform_factory, _get_base_form_class):
        """
        The get_form_class method should call down to modelform_factory
        """
        _get_base_form_class.return_value = Mock()
        self.omniform.get_form_class()
        modelform_factory.assert_called_with(
            self.omniform.content_type.model_class(),
            form=_get_base_form_class.return_value,
            fields=['foo', 'bar', 'baz'],
            formfield_callback=self.omniform.formfield_callback
        )

    @patch('omniforms.models.OmniModelForm._get_field')
    def test_formfield_callback(self, patched_method):
        """
        The formfield_callback method of the omniform should return a form field
        """
        field = Mock()
        field.name = 'title'
        self.omniform.formfield_callback(field)
        patched_method.assert_called_with('title')

    def test_get_field_labels(self):
        """
        The _get_field_labels method should return a labels dict for the form
        """
        labels = self.omniform._get_field_labels()
        self.assertEqual(labels['title'], 'Please give us a title')
        self.assertEqual(labels['agree'], 'Please agree')

    def test_get_initial_data(self):
        """
        The get_initial_data method of the form should return a dict of initial data
        """
        initial = self.omniform.get_initial_data()
        self.assertEqual(initial['title'], 'Some title...')
        self.assertEqual(initial['agree'], True)

    def test_get_model_field_choices(self):
        """
        The get_model_field_choices method should return the appropriate choice values
        """
        choices = self.omniform.get_model_field_choices()
        self.assertNotIn(('title', 'title'), choices)
        self.assertNotIn(('agree', 'agree'), choices)
        self.assertIn(('some_date', 'some date'), choices)
        self.assertIn(('some_datetime', 'some datetime'), choices)
        self.assertIn(('some_decimal', 'some decimal'), choices)
        self.assertIn(('some_email', 'some email'), choices)
        self.assertIn(('some_float', 'some float'), choices)
        self.assertIn(('some_integer', 'some integer'), choices)
        self.assertIn(('some_time', 'some time'), choices)
        self.assertIn(('some_url', 'some url'), choices)
        self.assertNotIn(('id', 'ID'), choices)

    @patch('omniforms.models.OmniModelForm.used_field_names',
           PropertyMock(return_value=['title', 'agree']))
    def test_get_model_field_choices_omits_used_fields(self):
        """
        The get_model_field_choices method should not include fields which have already been used
        """
        choices = self.omniform.get_model_field_choices()
        self.assertIn(('some_date', 'some date'), choices)
        self.assertIn(('some_datetime', 'some datetime'), choices)
        self.assertIn(('some_decimal', 'some decimal'), choices)
        self.assertIn(('some_email', 'some email'), choices)
        self.assertIn(('some_float', 'some float'), choices)
        self.assertIn(('some_integer', 'some integer'), choices)
        self.assertIn(('some_time', 'some time'), choices)
        self.assertIn(('some_url', 'some url'), choices)
        self.assertNotIn(('id', 'ID'), choices)
        self.assertNotIn(('title', 'title'), choices)
        self.assertNotIn(('agree', 'agree'), choices)

    @patch('omniforms.models.OmniFormEmailHandler.handle')
    def test_form_handle_method_calls_handlers(self, patched_method):
        """
        The forms 'handle' method should call each handler in turn
        """
        form_class = self.omniform.get_form_class()
        form = form_class({})
        form.full_clean()
        form.handle()
        self.assertEqual(patched_method.call_count, 2)
        patched_method.assert_any_call(form)

    @patch('omniforms.models.OmniFormEmailHandler.handle')
    def test_form_save_calls_handlers(self, patched_method):
        """
        The forms 'handle' method should call each handler in turn
        """
        form_class = self.omniform.get_form_class()
        form = form_class({})
        form.full_clean()
        form.save()
        self.assertEqual(patched_method.call_count, 2)
        patched_method.assert_any_call(form)

    def test_get_required_fields(self):
        """
        The get_required_fields method should return a list of required fields for the linked content model
        """
        get_field = self.omniform.content_type.model_class()._meta.get_field
        required_fields = self.omniform.get_required_fields(exclude_with_default=False)
        self.assertNotIn(get_field('id'), required_fields)
        self.assertIn(get_field('title'), required_fields)
        self.assertNotIn(get_field('agree'), required_fields)
        self.assertIn(get_field('some_datetime'), required_fields)
        self.assertNotIn(get_field('some_datetime_1'), required_fields)
        self.assertNotIn(get_field('some_datetime_2'), required_fields)
        self.assertIn(get_field('some_decimal'), required_fields)
        self.assertIn(get_field('some_email'), required_fields)
        self.assertIn(get_field('some_float'), required_fields)
        self.assertIn(get_field('some_integer'), required_fields)
        self.assertIn(get_field('some_time'), required_fields)
        self.assertNotIn(get_field('some_time_1'), required_fields)
        self.assertNotIn(get_field('some_time_2'), required_fields)
        self.assertIn(get_field('some_url'), required_fields)
        self.assertNotIn(get_field('some_date'), required_fields)
        self.assertNotIn(get_field('some_date_1'), required_fields)
        self.assertNotIn(get_field('some_date_2'), required_fields)
        self.assertNotIn(get_field('other_models'), required_fields)
        self.assertIn(get_field('slug'), required_fields)

    def test_get_required_fields_exclude_with_default(self):
        """
        The get_required_fields method should return a list of required fields for the linked content model
        """
        get_field = self.omniform.content_type.model_class()._meta.get_field
        required_fields = self.omniform.get_required_fields(exclude_with_default=True)
        self.assertNotIn(get_field('id'), required_fields)
        self.assertIn(get_field('title'), required_fields)
        self.assertNotIn(get_field('agree'), required_fields)
        self.assertIn(get_field('some_datetime'), required_fields)
        self.assertNotIn(get_field('some_datetime_1'), required_fields)
        self.assertNotIn(get_field('some_datetime_2'), required_fields)
        self.assertIn(get_field('some_decimal'), required_fields)
        self.assertIn(get_field('some_email'), required_fields)
        self.assertIn(get_field('some_float'), required_fields)
        self.assertIn(get_field('some_integer'), required_fields)
        self.assertIn(get_field('some_time'), required_fields)
        self.assertNotIn(get_field('some_time_1'), required_fields)
        self.assertNotIn(get_field('some_time_2'), required_fields)
        self.assertIn(get_field('some_url'), required_fields)
        self.assertNotIn(get_field('some_date'), required_fields)
        self.assertNotIn(get_field('some_date_1'), required_fields)
        self.assertNotIn(get_field('some_date_2'), required_fields)
        self.assertNotIn(get_field('other_models'), required_fields)
        self.assertIn(get_field('slug'), required_fields)

    def test_get_required_fields_defaults(self):
        """
        The get_required_fields method should return a list of required fields for the linked content model
        """
        get_field = self.omniform.content_type.model_class()._meta.get_field
        required_fields = self.omniform.get_required_fields()
        self.assertNotIn(get_field('id'), required_fields)
        self.assertIn(get_field('title'), required_fields)
        self.assertNotIn(get_field('agree'), required_fields)
        self.assertIn(get_field('some_datetime'), required_fields)
        self.assertNotIn(get_field('some_datetime_1'), required_fields)
        self.assertNotIn(get_field('some_datetime_2'), required_fields)
        self.assertIn(get_field('some_decimal'), required_fields)
        self.assertIn(get_field('some_email'), required_fields)
        self.assertIn(get_field('some_float'), required_fields)
        self.assertIn(get_field('some_integer'), required_fields)
        self.assertIn(get_field('some_time'), required_fields)
        self.assertNotIn(get_field('some_time_1'), required_fields)
        self.assertNotIn(get_field('some_time_2'), required_fields)
        self.assertIn(get_field('some_url'), required_fields)
        self.assertNotIn(get_field('some_date'), required_fields)
        self.assertNotIn(get_field('some_date_1'), required_fields)
        self.assertNotIn(get_field('some_date_2'), required_fields)
        self.assertNotIn(get_field('other_models'), required_fields)
        self.assertIn(get_field('slug'), required_fields)

    def test_get_required_field_names(self):
        """
        The get_required_field_names method should return a list of required field names for the linked content model
        """
        required_fields = self.omniform.get_required_field_names(exclude_with_default=False)
        self.assertNotIn('id', required_fields)
        self.assertIn('title', required_fields)
        self.assertNotIn('agree', required_fields)
        self.assertIn('some_datetime', required_fields)
        self.assertNotIn('some_datetime_1', required_fields)
        self.assertNotIn('some_datetime_2', required_fields)
        self.assertIn('some_decimal', required_fields)
        self.assertIn('some_email', required_fields)
        self.assertIn('some_float', required_fields)
        self.assertIn('some_integer', required_fields)
        self.assertIn('some_time', required_fields)
        self.assertNotIn('some_time_1', required_fields)
        self.assertNotIn('some_time_2', required_fields)
        self.assertIn('some_url', required_fields)
        self.assertNotIn('some_date', required_fields)
        self.assertNotIn('some_date_1', required_fields)
        self.assertNotIn('some_date_2', required_fields)
        self.assertNotIn('other_models', required_fields)
        self.assertIn('slug', required_fields)

    def test_used_field_names(self):
        """
        The used_field_names property of the model should return names of fields used on the form
        """
        used_field_names = self.omniform.used_field_names
        self.assertEqual(len(used_field_names), 2)
        self.assertIn('title', used_field_names)
        self.assertIn('agree', used_field_names)

    def test_get_model_fields(self):
        """
        The get_model_fields method of the form should return appropriate model fields
        """
        model_fields = self.omniform.get_model_fields()
        model_field_names = [field.name for field in model_fields]
        self.assertNotIn('id', model_field_names)
        self.assertNotIn('dummymodel3_set', model_field_names)
        self.assertIn('title', model_field_names)
        self.assertIn('agree', model_field_names)
        self.assertIn('some_date', model_field_names)
        self.assertIn('some_date_1', model_field_names)
        self.assertIn('some_date_2', model_field_names)
        self.assertIn('some_datetime', model_field_names)
        self.assertIn('some_datetime_1', model_field_names)
        self.assertIn('some_datetime_2', model_field_names)
        self.assertIn('some_decimal', model_field_names)
        self.assertIn('some_email', model_field_names)
        self.assertIn('some_float', model_field_names)
        self.assertIn('some_integer', model_field_names)
        self.assertIn('some_time', model_field_names)
        self.assertIn('some_time_1', model_field_names)
        self.assertIn('some_time_2', model_field_names)
        self.assertIn('some_url', model_field_names)
        self.assertIn('slug', model_field_names)
        self.assertIn('other_models', model_field_names)

    def test_get_model_field_names(self):
        """
        The get_model_field_names method should return the appropriate model field names
        """
        model_field_names = self.omniform.get_model_field_names()
        self.assertNotIn('id', model_field_names)
        self.assertNotIn('dummymodel3_set', model_field_names)
        self.assertIn('title', model_field_names)
        self.assertIn('agree', model_field_names)
        self.assertIn('some_date', model_field_names)
        self.assertIn('some_date_1', model_field_names)
        self.assertIn('some_date_2', model_field_names)
        self.assertIn('some_datetime', model_field_names)
        self.assertIn('some_datetime_1', model_field_names)
        self.assertIn('some_datetime_2', model_field_names)
        self.assertIn('some_decimal', model_field_names)
        self.assertIn('some_email', model_field_names)
        self.assertIn('some_float', model_field_names)
        self.assertIn('some_integer', model_field_names)
        self.assertIn('some_time', model_field_names)
        self.assertIn('some_time_1', model_field_names)
        self.assertIn('some_time_2', model_field_names)
        self.assertIn('some_url', model_field_names)
        self.assertIn('slug', model_field_names)
        self.assertIn('other_models', model_field_names)


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

    def test_name_field_invalid(self):
        """
        The name field should not validate if ti contains invalid characters
        """
        instance = OmniField(name='this is an invalid field name')
        try:
            instance.full_clean()
        except ValidationError as err:
            self.assertIn(
                'The name may only contain alphanumeric characters and underscores.',
                err.error_dict['name'][0].messages
            )
        else:
            self.fail('Validation error not raised')

    def test_name_field_valid(self):
        """
        The name field should validate
        """
        instance = OmniField(name='this_is_a_valid_field')
        try:
            instance.full_clean()
        except ValidationError as err:
            self.assertNotIn('name', err.error_dict)
        else:
            self.fail('Validation error not raised')

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

    def test_order_field(self):
        """
        The model should have an order field
        """
        field = OmniField._meta.get_field('order')
        self.assertIsInstance(field, models.IntegerField)
        self.assertEqual(field.default, 0)
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

    def test_real_type_field(self):
        """
        The model should have a real_type field
        """
        field = OmniField._meta.get_field('real_type')
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

    def test_get_concrete_class_for_model_field(self):
        """
        The get_concrete_class_for_model_field method should return the correct OmniField subclass
        """
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.CharField()), OmniCharField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.NullBooleanField()), OmniBooleanField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.BooleanField()), OmniBooleanField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DateTimeField()), OmniDateTimeField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DecimalField()), OmniDecimalField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.EmailField()), OmniEmailField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.FloatField()), OmniFloatField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.IntegerField()), OmniIntegerField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.BigIntegerField()), OmniIntegerField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.PositiveIntegerField()), OmniIntegerField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.SmallIntegerField()), OmniIntegerField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.TimeField()), OmniTimeField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.URLField()), OmniUrlField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.SlugField()), OmniSlugField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.FileField()), OmniFileField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.ImageField()), OmniImageField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DurationField()), OmniDurationField)
        self.assertEqual(
            OmniField.get_concrete_class_for_model_field(models.GenericIPAddressField()),
            OmniGenericIPAddressField
        )
        self.assertEqual(
            OmniField.get_concrete_class_for_model_field(models.CommaSeparatedIntegerField()),
            OmniCharField
        )
        self.assertEqual(
            OmniField.get_concrete_class_for_model_field(models.PositiveSmallIntegerField()),
            OmniIntegerField
        )
        self.assertEqual(
            OmniField.get_concrete_class_for_model_field(models.ForeignKey(DummyModel2)),
            OmniForeignKeyField
        )
        self.assertEqual(
            OmniField.get_concrete_class_for_model_field(models.ManyToManyField(DummyModel2)),
            OmniManyToManyField
        )

    @override_settings(OMNI_FORMS_CUSTOM_FIELD_MAPPING={
        'taggit_autosuggest.managers.TaggableManager': 'omniforms.tests.models.TaggableManagerField'
    })
    def test_get_custom_field_mapping(self):
        """
        The get_custom_field_mapping method of the class should return a mapping of custom fields
        """
        custom_field_mapping = OmniField.get_custom_field_mapping()
        self.assertIn(TaggableManager, custom_field_mapping)
        self.assertEqual(custom_field_mapping[TaggableManager], TaggableManagerField)

    @override_settings(OMNI_FORMS_CUSTOM_FIELD_MAPPING={
        'omniforms.tests.fields.ThisIsAFictionalField': 'omniforms.tests.models.TaggableManagerField'
    })
    def test_get_custom_field_mapping_raises_improperly_configured_exception_for_field(self):
        """
        The get_custom_field_mapping method of the class should raise an improperlyconfigured exception if the
        OMNI_FORMS_CUSTOM_FIELD_MAPPING setting contains a key that could not be imported
        """
        self.assertRaises(ImproperlyConfigured, OmniField.get_custom_field_mapping)

    @override_settings(OMNI_FORMS_CUSTOM_FIELD_MAPPING={
        'taggit_autosuggest.managers.TaggableManager': 'omniforms.tests.models.FictionalModel'
    })
    def test_get_custom_field_mapping_raises_improperly_configured_exception_for_model(self):
        """
        The get_custom_field_mapping method of the class should raise an improperlyconfigured exception if the
        OMNI_FORMS_CUSTOM_FIELD_MAPPING setting contains a value that could not be imported
        """
        self.assertRaises(ImproperlyConfigured, OmniField.get_custom_field_mapping)

    @override_settings(OMNI_FORMS_CUSTOM_FIELD_MAPPING={
        'taggit_autosuggest.managers.TaggableManager': 'omniforms.tests.models.TaggableManagerInvalidField'
    })
    def test_get_custom_field_mapping_raises_improperly_configured_exception_for_invalid_model(self):
        """
        The get_custom_field_mapping method of the class should raise an improperlyconfigured exception if the
        OMNI_FORMS_CUSTOM_FIELD_MAPPING imported model field does not subclass OmniField
        """
        self.assertRaises(ImproperlyConfigured, OmniField.get_custom_field_mapping)

    def test_field_name_unique_for_form(self):
        """
        The field name must be unique for the given form
        """
        form = OmniModelFormFactory.create()
        field = OmniField(name='A', label='A', widget_class='A', form=form)
        field.save()
        field.pk = None  # Remove the PK to make the instance think it's new
        self.assertRaises(IntegrityError, field.save)

    def test_get_edit_url_model_form(self):
        """
        The get_edit_url method should return the url for editing the resource in the django admin
        """
        form = OmniModelFormFactory.create()
        field = OmniField(name='A', label='A', widget_class='A', form=form)
        field.save()
        self.assertEqual(
            field.get_edit_url(),
            reverse('admin:omniforms_omnimodelform_updatefield', args=[field.object_id, field.name])
        )

    def test_get_edit_url_basic_form(self):
        """
        The get_edit_url method should return the url for editing the resource in the django admin
        """
        form = OmniFormFactory.create()
        field = OmniField(name='A', label='A', widget_class='A', form=form)
        field.save()
        self.assertEqual(
            field.get_edit_url(),
            reverse(
                'admin:omniforms_omniform_updatefield',
                args=[field.object_id, field.real_type_id, field.name]
            )
        )

    def test_get_concrete_models_manager_method(self):
        """
        The method should return the correct model classes
        """
        model_classes = OmniField.objects.get_concrete_models()
        for model_class in model_classes:
            self.assertTrue(issubclass(model_class, OmniField))
            self.assertNotEqual(model_class, OmniField)
            self.assertFalse(model_class._meta.abstract)


class OmniFieldInstanceTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniField model
    """
    def setUp(self):
        super(OmniFieldInstanceTestCase, self).setUp()
        self.field = OmniFloatField(
            name='Test Field',
            label='Test Field Label',
            help_text='Test help text',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            form=self.omni_form
        )
        self.field.save()

    def test_save_sets_real_type(self):
        """
        The OmniField save method should set the real_type field
        """
        self.assertEqual(self.field.real_type, ContentType.objects.get_for_model(OmniFloatField))

    def test_specific(self):
        """
        The specific property should return the specific instance
        """
        base_instance = OmniField.objects.get(pk=self.field.pk)
        instance = base_instance.specific
        self.assertIsInstance(base_instance, OmniField)
        self.assertNotIsInstance(base_instance, OmniFloatField)
        self.assertIsInstance(instance, OmniFloatField)

    def test_specific_returns_self(self):
        """
        The specific property should return the instance if it is already the most specific version
        """
        self.assertEqual(self.field, self.field.specific)

    def test_specific_cached(self):
        """
        The specific property should cache the result
        """
        base_instance = OmniField.objects.get(pk=self.field.pk)
        with patch.object(base_instance.real_type, 'get_object_for_this_type') as patched_method:
            patched_method.return_value = self.field
            assert base_instance.specific
            assert base_instance.specific
            self.assertEqual(patched_method.call_count, 1)

    def test_as_form_field(self):
        """
        The as_form_field method should return an instance of the correct field
        """
        field_class = import_string(self.field.FIELD_CLASS)
        widget_class = import_string(self.field.widget_class)
        instance = self.field.as_form_field()
        self.assertIsInstance(instance, field_class)
        self.assertEqual(self.field.label, instance.label)
        self.assertEqual(self.field.help_text, instance.help_text)
        self.assertTrue(self.field.required)
        self.assertIsInstance(instance.widget, widget_class)


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
        field = OmniCharField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.TextField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_length(self):
        """
        The model should have a max_length field
        """
        field = OmniCharField._meta.get_field('max_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.default, 255)

    def test_min_length(self):
        """
        The model should have a min_length field
        """
        field = OmniCharField._meta.get_field('min_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.default, 0)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniCharField.FIELD_CLASS, 'django.forms.CharField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.TextInput', OmniCharField.FORM_WIDGETS)
        self.assertIn('django.forms.widgets.Textarea', OmniCharField.FORM_WIDGETS)
        self.assertIn('django.forms.widgets.PasswordInput', OmniCharField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass the min_length and max_length to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniCharField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='Some title...',
            min_length=10,
            max_length=150,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.min_length, 10)
        self.assertEqual(field_instance.max_length, 150)


class OmniUUIDFieldTestCase(TestCase):
    """
    Tests the OmniUUIDField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniUUIDField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniUUIDField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.UUIDField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniUUIDField.FIELD_CLASS, 'django.forms.UUIDField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.TextInput', OmniUUIDField.FORM_WIDGETS)


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
        field = OmniBooleanField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.NullBooleanField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniBooleanField.FIELD_CLASS, 'django.forms.BooleanField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.CheckboxInput', OmniBooleanField.FORM_WIDGETS)


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
        field = OmniEmailField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.EmailField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_length(self):
        """
        The model should have a max_length field
        """
        field = OmniEmailField._meta.get_field('max_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.default, 255)

    def test_min_length(self):
        """
        The model should have a min_length field
        """
        field = OmniEmailField._meta.get_field('min_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.default, 0)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniEmailField.FIELD_CLASS, 'django.forms.EmailField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.EmailInput', OmniEmailField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass the min_length and max_length to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniEmailField(
            name='title',
            label='Please tell us your email address',
            required=True,
            widget_class='django.forms.widgets.EmailInput',
            order=0,
            initial_data='test@example.com',
            min_length=10,
            max_length=150,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.min_length, 10)
        self.assertEqual(field_instance.max_length, 150)


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
        field = OmniDateField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.DateField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniDateField.FIELD_CLASS, 'django.forms.DateField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.DateInput', OmniDateField.FORM_WIDGETS)


class OmniDurationFieldTestCase(TestCase):
    """
    Tests the OmniDurationField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniDurationField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniDurationField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.DurationField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniDurationField.FIELD_CLASS, 'django.forms.DurationField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.TextInput', OmniDurationField.FORM_WIDGETS)
        self.assertIn('django.forms.widgets.Textarea', OmniDurationField.FORM_WIDGETS)


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
        field = OmniDateTimeField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.DateTimeField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniDateTimeField.FIELD_CLASS, 'django.forms.DateTimeField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.DateTimeInput', OmniDateTimeField.FORM_WIDGETS)


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
        field = OmniDecimalField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.DecimalField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)
        self.assertEqual(field.decimal_places, 100)
        self.assertEqual(field.max_digits, 1000)

    def test_min_value(self):
        """
        The model should have a min_value field
        """
        field = OmniDecimalField._meta.get_field('min_value')
        self.assertIsInstance(field, models.DecimalField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_value(self):
        """
        The model should have a max_value field
        """
        field = OmniDecimalField._meta.get_field('max_value')
        self.assertIsInstance(field, models.DecimalField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_digits(self):
        """
        The model should have a max_digits field
        """
        field = OmniDecimalField._meta.get_field('max_digits')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_decimal_places(self):
        """
        The model should have a decimal_places field
        """
        field = OmniDecimalField._meta.get_field('decimal_places')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniDecimalField.FIELD_CLASS, 'django.forms.DecimalField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.NumberInput', OmniDecimalField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass protocol and unpack_ipv4 to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniDecimalField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data=10.8,
            min_value=0.0,
            max_value=999.987,
            max_digits=999,
            decimal_places=3,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.min_value, 0.0)
        self.assertEqual(field_instance.max_value, 999.987)
        self.assertEqual(field_instance.max_digits, 999)
        self.assertEqual(field_instance.decimal_places, 3)


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
        field = OmniFloatField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.FloatField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_min_value(self):
        """
        The model should have a min_value field
        """
        field = OmniFloatField._meta.get_field('min_value')
        self.assertIsInstance(field, models.FloatField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_value(self):
        """
        The model should have a max_value field
        """
        field = OmniFloatField._meta.get_field('max_value')
        self.assertIsInstance(field, models.FloatField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniFloatField.FIELD_CLASS, 'django.forms.FloatField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.NumberInput', OmniFloatField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass protocol and unpack_ipv4 to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniFloatField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.NumberInput',
            order=0,
            initial_data=10.8,
            min_value=10,
            max_value=999,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.min_value, 10)
        self.assertEqual(field_instance.max_value, 999)


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
        field = OmniIntegerField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.IntegerField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_min_value(self):
        """
        The model should have a min_value field
        """
        field = OmniIntegerField._meta.get_field('min_value')
        self.assertIsInstance(field, models.IntegerField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_value(self):
        """
        The model should have a max_value field
        """
        field = OmniIntegerField._meta.get_field('max_value')
        self.assertIsInstance(field, models.IntegerField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniIntegerField.FIELD_CLASS, 'django.forms.IntegerField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.NumberInput', OmniIntegerField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass protocol and unpack_ipv4 to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniIntegerField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.NumberInput',
            order=0,
            initial_data=10,
            min_value=5,
            max_value=999,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.min_value, 5)
        self.assertEqual(field_instance.max_value, 999)


class OmniGenericIPAddressFieldTestCase(TestCase):
    """
    Tests the OmniGenericIPAddressField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniGenericIPAddressField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniGenericIPAddressField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.GenericIPAddressField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_protocol(self):
        """
        The model should have a protocol field
        """
        field = OmniGenericIPAddressField._meta.get_field('protocol')
        self.assertIsInstance(field, models.CharField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.max_length, 4)
        self.assertEqual(field.choices, OmniGenericIPAddressField.PROTOCOL_CHOICES)
        self.assertEqual(field.default, OmniGenericIPAddressField.PROTOCOL_BOTH)

    def test_unpack_ipv4(self):
        """
        The model should have an unpack_ipv4 field
        """
        field = OmniGenericIPAddressField._meta.get_field('unpack_ipv4')
        self.assertIsInstance(field, models.BooleanField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertFalse(field.default)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniGenericIPAddressField.FIELD_CLASS, 'django.forms.GenericIPAddressField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.TextInput', OmniGenericIPAddressField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass protocol and unpack_ipv4 to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniGenericIPAddressField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='192.168.1.1',
            protocol=OmniGenericIPAddressField.PROTOCOL_BOTH,
            unpack_ipv4=True,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.validators[0].__name__, 'validate_ipv46_address')
        self.assertTrue(field_instance.unpack_ipv4)

    def test_unpack_ipv4_raises_validation_error_with_ipv4(self):
        """
        The clean method should raise a validation error if unpack_ipv4 is selected with any protocol other than both
        """
        form = OmniModelFormFactory.create()
        field = OmniGenericIPAddressField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='192.168.1.1',
            protocol=OmniGenericIPAddressField.PROTOCOL_IPV4,
            unpack_ipv4=True,
            form=form
        )
        self.assertRaises(ValidationError, field.full_clean)

    def test_unpack_ipv4_raises_validation_error_with_ipv6(self):
        """
        The clean method should raise a validation error if unpack_ipv4 is selected with any protocol other than both
        """
        form = OmniModelFormFactory.create()
        field = OmniGenericIPAddressField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='192.168.1.1',
            protocol=OmniGenericIPAddressField.PROTOCOL_IPV6,
            unpack_ipv4=True,
            form=form
        )
        self.assertRaises(ValidationError, field.full_clean)

    def test_unpack_ipv4_cleans_without_error(self):
        """
        The clean method should not raise a validation error if unpack_ipv4 is selected with protocol both
        """
        form = OmniModelFormFactory.create()
        field = OmniGenericIPAddressField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='192.168.1.1',
            protocol=OmniGenericIPAddressField.PROTOCOL_BOTH,
            unpack_ipv4=True,
            form=form
        )
        field.save()
        field.full_clean()


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
        field = OmniTimeField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.TimeField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniTimeField.FIELD_CLASS, 'django.forms.TimeField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.TimeInput', OmniTimeField.FORM_WIDGETS)


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
        field = OmniUrlField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.URLField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_max_length(self):
        """
        The model should have a max_length field
        """
        field = OmniUrlField._meta.get_field('max_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.default, 255)

    def test_min_length(self):
        """
        The model should have a min_length field
        """
        field = OmniUrlField._meta.get_field('min_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertFalse(field.null)
        self.assertEqual(field.default, 0)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniUrlField.FIELD_CLASS, 'django.forms.URLField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.URLInput', OmniUrlField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass the min_length and max_length to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniUrlField(
            name='title',
            label='Please give us a title',
            required=True,
            widget_class='django.forms.widgets.TextInput',
            order=0,
            initial_data='http://www.google.com',
            min_length=10,
            max_length=150,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.min_length, 10)
        self.assertEqual(field_instance.max_length, 150)


class OmniSlugFieldTestCase(TestCase):
    """
    Tests the OmniSlugField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniSlugField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        field = OmniSlugField._meta.get_field('initial_data')
        self.assertIsInstance(field, models.SlugField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniSlugField.FIELD_CLASS, 'django.forms.SlugField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.TextInput', OmniSlugField.FORM_WIDGETS)
        self.assertIn('django.forms.widgets.HiddenInput', OmniSlugField.FORM_WIDGETS)


class OmniFileFieldTestCase(TestCase):
    """
    Tests the OmniFileField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniFileField, OmniField))

    def test_initial(self):
        """
        The model should not allow initial data
        """
        self.assertIsNone(OmniFileField.initial_data)

    def test_max_length(self):
        """
        The model should define a max_length field
        """
        field = OmniFileField._meta.get_field('max_length')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_allow_empty_file(self):
        """
        The model should not define a allow_empty_file field
        """
        field = OmniFileField._meta.get_field('allow_empty_file')
        self.assertIsInstance(field, models.BooleanField)
        self.assertFalse(field.default)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniFileField.FIELD_CLASS, 'django.forms.FileField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.FileInput', OmniFileField.FORM_WIDGETS)

    def test_as_form_field(self):
        """
        The as_form_field method should pass the min_length and max_length to the field constructor
        """
        form = OmniModelFormFactory.create()
        field = OmniFileField(
            name='my_file',
            label='Please upload a file',
            required=True,
            widget_class='django.forms.widgets.FileInput',
            order=0,
            max_length=150,
            allow_empty_file=True,
            form=form
        )
        field.save()
        field_instance = field.as_form_field()
        self.assertEqual(field_instance.max_length, 150)
        self.assertTrue(field_instance.allow_empty_file)


class OmniImageFieldTestCase(TestCase):
    """
    Tests the OmniImageField
    """
    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniImageField
        """
        self.assertTrue(issubclass(OmniImageField, OmniField))

    def test_initial(self):
        """
        The model should not allow initial data
        """
        self.assertIsNone(OmniImageField.initial_data)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniImageField.FIELD_CLASS, 'django.forms.ImageField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.widgets.FileInput', OmniImageField.FORM_WIDGETS)


class OmniManyToManyFieldTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniManyToManyField
    """
    def setUp(self):
        super(OmniManyToManyFieldTestCase, self).setUp()
        self.field = OmniManyToManyField(
            related_type=ContentType.objects.get_for_model(Permission),
            name='Test Field',
            label='Test Field Label',
            help_text='Test help text',
            required=True,
            widget_class=OmniManyToManyField.FORM_WIDGETS[0],
            form=self.omni_form
        )
        self.field.save()

    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniManyToManyField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        self.assertIsNone(OmniManyToManyField.initial_data)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniManyToManyField.FIELD_CLASS, 'django.forms.ModelMultipleChoiceField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.SelectMultiple', OmniManyToManyField.FORM_WIDGETS)
        self.assertIn('django.forms.CheckboxSelectMultiple', OmniManyToManyField.FORM_WIDGETS)

    def test_related_type_field(self):
        """
        The model should define a related_type field
        """
        field = OmniManyToManyField._meta.get_field('related_type')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.rel.to, ContentType)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_as_form_field(self):
        """
        The as_form_field method should set the queryset
        """
        field_class = import_string(self.field.FIELD_CLASS)
        widget_class = import_string(self.field.widget_class)
        instance = self.field.as_form_field()
        self.assertIsInstance(instance, field_class)
        self.assertEqual(self.field.label, instance.label)
        self.assertEqual(self.field.help_text, instance.help_text)
        self.assertTrue(self.field.required)
        self.assertIsInstance(instance.widget, widget_class)
        self.assertEquals(list(instance.queryset), list(Permission.objects.all()))


class OmniForeignKeyFieldTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniForeignKeyField
    """
    def setUp(self):
        super(OmniForeignKeyFieldTestCase, self).setUp()
        self.field = OmniForeignKeyField(
            related_type=ContentType.objects.get_for_model(Permission),
            name='Test Field',
            label='Test Field Label',
            help_text='Test help text',
            required=True,
            widget_class=OmniForeignKeyField.FORM_WIDGETS[0],
            form=self.omni_form
        )
        self.field.save()

    def test_subclasses_omni_field(self):
        """
        The model should subclass OmniField
        """
        self.assertTrue(issubclass(OmniForeignKeyField, OmniField))

    def test_initial(self):
        """
        The model should have an initial field
        """
        self.assertIsNone(OmniForeignKeyField.initial_data)

    def test_field_class(self):
        """
        The model should define the correct field class
        """
        self.assertEqual(OmniForeignKeyField.FIELD_CLASS, 'django.forms.ModelChoiceField')

    def test_form_widgets(self):
        """
        The model should define the correct form widgets
        """
        self.assertIn('django.forms.Select', OmniForeignKeyField.FORM_WIDGETS)
        self.assertIn('django.forms.RadioSelect', OmniForeignKeyField.FORM_WIDGETS)

    def test_related_type_field(self):
        """
        The model should define a related_type field
        """
        field = OmniForeignKeyField._meta.get_field('related_type')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.rel.to, ContentType)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_as_form_field(self):
        """
        The as_form_field method should set the queryset
        """
        field_class = import_string(self.field.FIELD_CLASS)
        widget_class = import_string(self.field.widget_class)
        instance = self.field.as_form_field()
        self.assertIsInstance(instance, field_class)
        self.assertEqual(self.field.label, instance.label)
        self.assertEqual(self.field.help_text, instance.help_text)
        self.assertTrue(self.field.required)
        self.assertIsInstance(instance.widget, widget_class)
        self.assertEquals(list(instance.queryset), list(Permission.objects.all()))


class OmniChoiceFieldTestCase(TestCase):
    """
    Tests the OmniChoiceField model
    """
    def test_inheritance(self):
        """
        The model should inherit from OmniField
        """
        self.assertTrue(issubclass(OmniChoiceField, OmniField))

    def test_initial_data(self):
        """
        The model should have no initial data
        """
        self.assertIsNone(OmniChoiceField.initial_data)

    def test_choices_field(self):
        """
        The model should have a choices field
        """
        field = OmniChoiceField._meta.get_field('choices')
        self.assertIsInstance(field, models.TextField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_field_class(self):
        """
        The model should have an appropriate field class
        """
        self.assertEqual(OmniChoiceField.FIELD_CLASS, 'django.forms.ChoiceField')

    def test_form_widgets(self):
        """
        The model should have appropriate field widgets defined
        """
        self.assertIn('django.forms.widgets.Select', OmniChoiceField.FORM_WIDGETS)
        self.assertIn('django.forms.widgets.RadioSelect', OmniChoiceField.FORM_WIDGETS)

    def test_as_form_field_choices(self):
        """
        The method should generate the correct form field choices
        """
        form = OmniForm.objects.create(title='Dummy form')
        instance = OmniChoiceField.objects.create(
            name='choices',
            label='choices',
            widget_class='django.forms.widgets.Select',
            choices='foo\n\n   bar \n\n\n baz',
            form=form
        )
        field = instance.as_form_field()

        self.assertEqual(3, len(field.choices))
        self.assertIn(['foo', 'foo'], field.choices)
        self.assertIn(['bar', 'bar'], field.choices)
        self.assertIn(['baz', 'baz'], field.choices)


class OmniMultipleChoiceFieldTestCase(TestCase):
    """
    Tests the OmniMultipleChoiceField model
    """
    def test_inheritance(self):
        """
        The model should inherit from OmniField
        """
        self.assertTrue(issubclass(OmniMultipleChoiceField, OmniField))

    def test_initial_data(self):
        """
        The model should have no initial data
        """
        self.assertIsNone(OmniMultipleChoiceField.initial_data)

    def test_choices_field(self):
        """
        The model should have a choices field
        """
        field = OmniMultipleChoiceField._meta.get_field('choices')
        self.assertIsInstance(field, models.TextField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_field_class(self):
        """
        The model should have an appropriate field class
        """
        self.assertEqual(OmniMultipleChoiceField.FIELD_CLASS, 'django.forms.MultipleChoiceField')

    def test_form_widgets(self):
        """
        The model should have appropriate field widgets defined
        """
        self.assertIn('django.forms.widgets.SelectMultiple', OmniMultipleChoiceField.FORM_WIDGETS)
        self.assertIn('django.forms.widgets.CheckboxSelectMultiple', OmniMultipleChoiceField.FORM_WIDGETS)

    def test_as_form_field_choices(self):
        """
        The method should generate the correct form field choices
        """
        form = OmniForm.objects.create(title='Dummy form')
        instance = OmniMultipleChoiceField.objects.create(
            name='choices',
            label='choices',
            widget_class='django.forms.widgets.SelectMultiple',
            choices='foo\n\n   bar \n\n\n baz',
            form=form
        )
        field = instance.as_form_field()

        self.assertEqual(3, len(field.choices))
        self.assertIn(['foo', 'foo'], field.choices)
        self.assertIn(['bar', 'bar'], field.choices)
        self.assertIn(['baz', 'baz'], field.choices)


class OmniFormHandlerTestCase(TestCase):
    """
    Tests the OmniFormHandler class
    """
    def test_name_field(self):
        """
        The model should have a name field
        """
        field = OmniFormHandler._meta.get_field('name')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_order_field(self):
        """
        The model should have an order field
        """
        field = OmniFormHandler._meta.get_field('order')
        self.assertIsInstance(field, models.IntegerField)
        self.assertEqual(field.default, 0)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_content_type_field(self):
        """
        The model should have a content_type field
        """
        field = OmniFormHandler._meta.get_field('content_type')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.rel.to, ContentType)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_object_id_field(self):
        """
        The model should have an object_id field
        """
        field = OmniFormHandler._meta.get_field('object_id')
        self.assertIsInstance(field, models.PositiveIntegerField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_form(self):
        """
        The model should have a 'form' field
        """
        field = OmniFormHandler.form
        self.assertIsInstance(field, GenericForeignKey)

    def test_string_representation(self):
        """
        The models name should be used as the string representation of the instance
        """
        instance = OmniFormHandler(name='Test handler')
        self.assertEqual(instance.name, '{0}'.format(instance))

    def test_handle_raises_not_implemented_error(self):
        """
        The handle method should raise a NotImplementedError
        """
        instance = OmniFormHandler(name='Test handler')
        self.assertRaises(NotImplementedError, instance.handle, Mock())

    def test_get_edit_url_model_form(self):
        """
        The get_edit_url method should return the url for editing the resource in the django admin
        """
        form = OmniModelFormFactory.create()
        instance = OmniFormHandler(name='Test handler', form=form)
        instance.save()
        self.assertEqual(
            instance.get_edit_url(),
            reverse('admin:omniforms_omnimodelform_updatehandler', args=[instance.object_id, instance.pk])
        )

    def test_get_edit_url_basic_form(self):
        """
        The get_edit_url method should return the url for editing the resource in the django admin
        """
        form = OmniFormFactory.create()
        instance = OmniFormHandler(name='Test handler', form=form)
        instance.save()
        self.assertEqual(
            instance.get_edit_url(),
            reverse('admin:omniforms_omniform_updatehandler', args=[instance.object_id, instance.pk])
        )

    def test_get_concrete_models_manager_method(self):
        """
        The method should return the correct model classes
        """
        model_classes = OmniFormHandler.objects.get_concrete_models()
        for model_class in model_classes:
            self.assertTrue(issubclass(model_class, OmniFormHandler))
            self.assertNotEqual(model_class, OmniFormHandler)
            self.assertFalse(model_class._meta.abstract)


class TemplateHelpTextLazyTestCase(OmniModelFormTestCaseStub):
    """
    Tests the TemplateHelpTextLazy class
    """
    def setUp(self):
        super(TemplateHelpTextLazyTestCase, self).setUp()
        self.handler = OmniFormEmailHandler(
            name='Send Email',
            order=0,
            template='Hello {{ user }}',
            recipients='a@example.com,b@example.com',
            subject='This is a test',
            form=self.omni_form
        )
        self.handler.save()

    def test_generates_help_text(self):
        """
        The instance should generate appropriate help text
        """
        self.title_field = OmniCharField.objects.create(name='title', label='title', form=self.omni_form)
        self.agree_field = OmniBooleanField.objects.create(name='agree', label='agree', form=self.omni_form)
        self.some_date_field = OmniCharField.objects.create(name='some_date', label='some_date', form=self.omni_form)
        self.instance = TemplateHelpTextLazy(self.handler)
        self.assertEqual(
            '{0}'.format(self.instance),
            'Please enter the content of the email here. '
            'Available tokens are {{ title }}, {{ agree }}, {{ some_date }}'
        )

    def test_generates_simple_help_text(self):
        """
        The instance should generate appropriate help text
        """
        self.instance = TemplateHelpTextLazy(self.handler)
        self.assertEqual(
            '{0}'.format(self.instance),
            'Please enter the content of the email here.'
        )


class OmniFormHandlerInstanceTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniFormHandler class
    """
    def setUp(self):
        super(OmniFormHandlerInstanceTestCase, self).setUp()
        self.handler = OmniFormEmailHandler(
            name='Send Email',
            order=0,
            template='Hello {{ user }}',
            recipients='a@example.com,b@example.com',
            subject='This is a test',
            form=self.omni_form
        )
        self.handler.save()

    def test_save_sets_real_type(self):
        """
        The OmniField save method should set the real_type field
        """
        self.assertEqual(self.handler.real_type, ContentType.objects.get_for_model(OmniFormEmailHandler))

    def test_specific(self):
        """
        The specific property should return the specific instance
        """
        base_instance = OmniFormHandler.objects.get(pk=self.handler.pk)
        instance = base_instance.specific
        self.assertIsInstance(base_instance, OmniFormHandler)
        self.assertNotIsInstance(base_instance, OmniFormEmailHandler)
        self.assertIsInstance(instance, OmniFormEmailHandler)

    def test_specific_returns_self(self):
        """
        The specific property should return the instance if it is already the most specific version
        """
        self.assertEqual(self.handler, self.handler.specific)

    def test_specific_cached(self):
        """
        The specific property should cache the result
        """
        base_instance = OmniFormHandler.objects.get(pk=self.handler.pk)
        with patch.object(base_instance.real_type, 'get_object_for_this_type') as patched_method:
            patched_method.return_value = self.handler
            assert base_instance.specific
            assert base_instance.specific
            self.assertEqual(patched_method.call_count, 1)


class OmniFormEmailHandlerTestCase(TestCase):
    """
    Tests the OmniFormEmailHandler
    """
    def setUp(self):
        super(OmniFormEmailHandlerTestCase, self).setUp()
        self.pdf_file = open(os.path.join(TEST_FILE_DIR, 'tests', 'files', 'test.pdf'), 'rb')
        self.image_file = open(os.path.join(TEST_FILE_DIR, 'tests', 'files', 'blank.gif'), 'rb')

    def test_extends_base_class(self):
        """
        The model should extend OmniFormHandler
        """
        self.assertTrue(issubclass(OmniFormEmailHandler, OmniFormHandler))

    def test_template_help_text(self):
        """
        The 'template' fields help text should be an instance of TemplateHelpTextLazy
        """
        instance = OmniFormEmailHandler(
            template='Hello {{ user }}',
            recipients='a@example.com,b@example.com',
            subject='This is a test'
        )
        self.assertIsInstance(instance._meta.get_field('template').help_text, TemplateHelpTextLazy)

    def test_recipients_field(self):
        """
        The model should define a recipients field
        """
        field = OmniFormEmailHandler._meta.get_field('recipients')
        self.assertIsInstance(field, models.TextField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_subject_field(self):
        """
        The model should define a subject field
        """
        field = OmniFormEmailHandler._meta.get_field('subject')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_template_field(self):
        """
        The model should define a template field
        """
        field = OmniFormEmailHandler._meta.get_field('template')
        self.assertIsInstance(field, models.TextField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_render_template(self):
        """
        The _render_template method should return the rendered template
        """
        instance = OmniFormEmailHandler(template='Hello {{ user }}')
        self.assertEqual('Hello Bob', instance._render_template({'user': 'Bob'}))

    @override_settings(DEFAULT_FROM_EMAIL='administrator@example.com')
    @patch('omniforms.models.EmailMessage.__init__')
    @patch('omniforms.models.EmailMessage.send')
    def test_handle(self, send, init):
        """
        The handle method should send an email
        """
        init.return_value = None
        form = Mock(attributes=['cleaned_data'])
        form.cleaned_data = {'user': 'Bob'}
        instance = OmniFormEmailHandler(
            template='Hello {{ user }}',
            recipients='a@example.com,b@example.com',
            subject='This is a test'
        )
        instance.handle(form)
        init.assert_called_with(
            'This is a test',
            'Hello Bob',
            'administrator@example.com',
            ['a@example.com', 'b@example.com']
        )
        send.assert_called_with()

    @patch('omniforms.models.EmailMessage.attach')
    @patch('django.core.files.uploadedfile.InMemoryUploadedFile.read', Mock(return_value='Content'))
    def test_attaches_files(self, patched_method):
        """
        Uploaded files should be attached to the email
        """
        pdf = InMemoryUploadedFile(self.pdf_file, None, 'test.pdf', 'application/pdf', 1024, None)
        gif = InMemoryUploadedFile(self.image_file, None, 'test.gif', 'image/gif', 1024, None)
        form = Mock(attributes=['cleaned_data'])
        form.cleaned_data = {'user': 'Bob', 'pdf': pdf, 'gif': gif}
        instance = OmniFormEmailHandler(
            template='Hello {{ user }}',
            recipients='a@example.com,b@example.com',
            subject='This is a test'
        )
        instance.handle(form)
        patched_method.assert_any_call('test.pdf', 'Content', 'application/pdf')
        patched_method.assert_any_call('test.gif', 'Content', 'image/gif')


class EmailConfirmationHandlerTestCase(TestCase):
    """
    Tests the EmailConfirmationHandler model
    """
    def setUp(self):
        super(EmailConfirmationHandlerTestCase, self).setUp()
        self.form = OmniFormFactory.create()
        self.email_field = OmniEmailFieldFactory.create(
            form=self.form,
            name='email'
        )
        self.handler = OmniFormEmailConfirmationHandlerFactory.create(
            form=self.form,
            recipient_field=self.email_field,
            template='Dear {{ email }}\nThanks for contacting us'
        )

    def test_inheritance(self):
        """
        The model should inherit from OmniFormHandler
        """
        self.assertTrue(issubclass(OmniFormEmailConfirmationHandler, OmniFormHandler))

    def test_subject_field(self):
        """
        The model should have a subject field
        """
        field = OmniFormEmailConfirmationHandler._meta.get_field('subject')
        self.assertIsInstance(field, models.CharField)
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_recipient_field_field(self):
        """
        The model should have a recipient_field field
        """
        field = OmniFormEmailConfirmationHandler._meta.get_field('recipient_field')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.rel.to, OmniEmailField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_template_field(self):
        """
        The model should have a template field
        """
        field = OmniFormEmailConfirmationHandler._meta.get_field('template')
        self.assertIsInstance(field, models.TextField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_base_form_class(self):
        """
        The model should define the correct base form class
        """
        self.assertEqual(
            OmniFormEmailConfirmationHandler.base_form_class,
            EmailConfirmationHandlerBaseFormClass
        )

    def test_cannot_delete_email_field_if_referenced_by_handler(self):
        """
        It should not be possible to delete the email field if it is referenced by the handler
        """
        self.assertRaises(ProtectedError, self.email_field.delete)

    def test_handle_sends_email(self):
        """
        The handle method should send an email
        """
        form_class = self.form.get_form_class()
        form = form_class({'email': 'someone@example.com'})
        self.assertTrue(form.is_valid())
        self.handler.handle(form)

        msg = mail.outbox[0]

        self.assertEqual(len(mail.outbox), 1)
        self.assertListEqual(msg.recipients(), ['someone@example.com'])
        self.assertEqual(msg.subject, self.handler.subject)
        self.assertEqual('Dear someone@example.com\nThanks for contacting us', msg.body)


class OmniFormSaveInstanceHandlerTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniFormSaveInstanceHandler
    """
    def setUp(self):
        super(OmniFormSaveInstanceHandlerTestCase, self).setUp()
        self.handler = OmniFormSaveInstanceHandler(
            name='Save instance',
            order=0,
            form=self.omni_form
        )
        self.handler.save()

    def test_extends_base_class(self):
        """
        The model should extend OmniFormHandler
        """
        self.assertTrue(issubclass(OmniFormSaveInstanceHandler, OmniFormHandler))

    @skipUnless(django.VERSION < (1, 9, 0, 'final', 0), 'Tests functionality specific to django versions < 1.9')
    @patch('django.forms.models.save_instance')
    def test_handle_django_lte_18(self, patched_method):
        """
        The handle method should call down to the save_instance function
        """
        dummy_model = DummyModelFactory.create()
        form_class = self.omni_form.get_form_class()
        form = form_class(instance=dummy_model, data={})
        instance = OmniFormSaveInstanceHandler()
        instance.handle(form)
        patched_method.assert_called_with(
            form, form.instance, form._meta.fields,
            'changed', True, form._meta.exclude,
            construct=False
        )

    @skipUnless(django.VERSION >= (1, 9, 0, 'final', 0), 'Tests functionality specific to django versions >= 1.9')
    def test_handle(self):
        """
        The handle method should call down to the save_instance function
        """
        dummy_model = DummyModelFactory.create()
        with patch.object(dummy_model, 'save') as patched_method:
            form_class = self.omni_form.get_form_class()
            form = form_class(instance=dummy_model, data={
                'title': 'title',
                'agree': True,
                'some_datetime': timezone.now(),
                'some_decimal': 0.3,
                'some_email': 'test@example.com',
                'some_float': 1.0,
                'some_integer': 2,
                'some_time': timezone.now().time(),
                'some_url': 'http://www.google.com'
            })
            form.full_clean()
            instance = OmniFormSaveInstanceHandler()
            instance.handle(form)
            patched_method.assert_called_once()

    def test_cannot_be_attached_to_non_model_form(self):
        """
        It must not be possible to attach the Save Instance handler to non model forms
        """
        form = OmniForm(title='Test form')
        form.save()
        handler = OmniFormSaveInstanceHandler(name='Save instance', order=0, form=form)
        with self.assertRaises(ValidationError) as cm:
            handler.clean()
        self.assertEqual(cm.exception.message, 'This handler can only be attached to model forms')

    @patch('omniforms.models.OmniFormSaveInstanceHandler.assert_has_all_required_fields')
    def test_clean_calls_assert_has_all_required_fields(self, patched_method):
        """
        The clean method should call down to assert_has_all_required_fields
        """
        handler = OmniFormSaveInstanceHandler(name='Save instance', order=0, form=self.omni_form)
        handler.clean()
        patched_method.assert_called_with()

    @patch('omniforms.models.OmniModelForm.used_field_names',
           PropertyMock(return_value=['foo', 'something', 'else']))
    @patch('omniforms.models.OmniModelForm.get_required_field_names')
    def test_assert_has_all_required_fields_invalid(self, get_required_field_names):
        """
        The assert_has_all_required_fields method should raise a ValidationError with an appropriate message
        """
        get_required_field_names.return_value = ['foo', 'bar', 'baz']
        handler = OmniFormSaveInstanceHandler(name='Save instance', order=0, form=self.omni_form)
        with self.assertRaises(ValidationError) as cm:
            handler.assert_has_all_required_fields()

        self.assertEqual(
            cm.exception.message,
            'The save instance handler can only be attached to forms that contain fields for '
            'all required model fields.  The form you are attempting to attach this handler to '
            'is missing the following fields: ({0})'.format(', '.join(['bar', 'baz']))
        )

    @patch('omniforms.models.OmniModelForm.used_field_names',
           PropertyMock(return_value=['foo', 'bar', 'baz', 'something', 'else']))
    @patch('omniforms.models.OmniModelForm.get_required_field_names')
    def test_assert_has_all_required_fields_valid(self, get_required_field_names):
        """
        The assert_has_all_required_fields method should not raise a ValidationError
        """
        get_required_field_names.return_value = ['foo', 'bar', 'baz']
        handler = OmniFormSaveInstanceHandler(name='Save instance', order=0, form=self.omni_form)
        handler.assert_has_all_required_fields()
