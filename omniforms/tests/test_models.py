# -*- coding: utf-8 -*-
"""
Tests the omniforms models
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase, override_settings
from django.utils.module_loading import import_string
from mock import Mock, patch
from omniforms.forms import OmniModelFormBaseForm
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
    OmniManyToManyField,
    OmniForeignKeyField,
    OmniFormHandler,
    OmniFormEmailHandler
)
from omniforms.tests.utils import OmniFormTestCaseStub
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


class OmniFormTestCase(OmniFormTestCaseStub):
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
        self.handler_1 = OmniFormEmailHandler(
            subject='test',
            recipients='test@example.com',
            template='Test content',
            name='test 1',
            order=0,
            form=self.omniform
        )
        self.handler_1.save()
        self.handler_2 = OmniFormEmailHandler(
            subject='test2',
            recipients='test2@example.com',
            template='Test content 2',
            name='test 2',
            order=1,
            form=self.omniform
        )
        self.handler_2.save()

    def test_get_form_class(self):
        """
        The get_form_class method should return a form class
        """
        form_class = self.omniform.get_form_class()
        self.assertTrue(issubclass(form_class, OmniModelFormBaseForm))

    def test_get_model_field_choices(self):
        """
        The get_model_field_choices method should return the appropriate choice values
        """
        choices = self.omniform.get_model_field_choices()
        self.assertIn(('title', 'title'), choices)
        self.assertIn(('agree', 'agree'), choices)
        self.assertIn(('some_date', 'some date'), choices)
        self.assertIn(('some_datetime', 'some datetime'), choices)
        self.assertIn(('some_decimal', 'some decimal'), choices)
        self.assertIn(('some_email', 'some email'), choices)
        self.assertIn(('some_float', 'some float'), choices)
        self.assertIn(('some_integer', 'some integer'), choices)
        self.assertIn(('some_time', 'some time'), choices)
        self.assertIn(('some_url', 'some url'), choices)
        self.assertNotIn(('id', 'ID'), choices)

    @patch('omniforms.models.OmniModelForm.get_used_field_names')
    def test_get_model_field_choices_omits_used_fields(self, patched_method):
        """
        The get_model_field_choices method should not include fields which have already been used
        """
        patched_method.return_value = ['title', 'agree']
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
        patched_method.assert_any_call({})

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
        patched_method.assert_any_call({})


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
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.BooleanField()), OmniBooleanField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DateTimeField()), OmniDateTimeField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.DecimalField()), OmniDecimalField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.EmailField()), OmniEmailField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.FloatField()), OmniFloatField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.IntegerField()), OmniIntegerField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.TimeField()), OmniTimeField)
        self.assertEqual(OmniField.get_concrete_class_for_model_field(models.URLField()), OmniUrlField)


class OmniFieldInstanceTestCase(OmniFormTestCaseStub):
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
        field = OmniCharField._meta.get_field('initial')
        self.assertIsInstance(field, models.TextField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

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
        field = OmniEmailField._meta.get_field('initial')
        self.assertIsInstance(field, models.EmailField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

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
        field = OmniDecimalField._meta.get_field('initial')
        self.assertIsInstance(field, models.DecimalField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)
        self.assertEqual(field.decimal_places, 2)
        self.assertEqual(field.max_digits, 10)

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
        field = OmniUrlField._meta.get_field('initial')
        self.assertIsInstance(field, models.URLField)
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

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


class OmniManyToManyFieldTestCase(OmniFormTestCaseStub):
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
        self.assertIsNone(OmniManyToManyField.initial)

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


class OmniForeignKeyFieldTestCase(OmniFormTestCaseStub):
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
        self.assertIsNone(OmniForeignKeyField.initial)

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


class OmniFormHandlerInstanceTestCase(OmniFormTestCaseStub):
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
    def test_extends_base_class(self):
        """
        The model should extend OmniFormHandler
        """
        self.assertTrue(issubclass(OmniFormEmailHandler, OmniFormHandler))

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
    @patch('omniforms.models.send_mail')
    def test_handle(self, patched_method):
        """
        The handle method should send an email
        """
        form = Mock(attributes=['cleaned_data'])
        form.cleaned_data = {'user': 'Bob'}
        instance = OmniFormEmailHandler(
            template='Hello {{ user }}',
            recipients='a@example.com,b@example.com',
            subject='This is a test'
        )
        instance.handle(form)
        patched_method.assert_called_with(
            'This is a test',
            'Hello Bob',
            'administrator@example.com',
            ['a@example.com', 'b@example.com'],
            fail_silently=False
        )
