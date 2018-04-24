# -*- coding: utf-8 -*-
"""
Tests the omniforms admin forms
"""
from __future__ import unicode_literals
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils import timezone
from mock import Mock, patch
from omniforms.forms import OmniFormBaseForm, OmniModelFormBaseForm, EmailConfirmationHandlerBaseFormClass
from omniforms.models import OmniFormEmailConfirmationHandler
from omniforms.tests.factories import OmniFormFactory, OmniEmailFieldFactory
from omniforms.tests.models import DummyModel


class OmniFormBaseFormTestCase(TestCase):
    """
    Tests the OmniFormBaseForm
    """
    def setUp(self):
        super(OmniFormBaseFormTestCase, self).setUp()
        self.mock_1 = Mock(methods=['handle'])
        self.mock_2 = Mock(methods=['handle'])
        self.form = OmniFormBaseForm({})
        self.form._handlers = [self.mock_1, self.mock_2]

    def test_form_handle_calls_handlers(self):
        """
        The forms handle method should call down to each handlers handle method
        """
        self.form.full_clean()
        self.form.handle()
        self.mock_1.handle.assert_called_once()
        self.mock_2.handle.assert_called_once()

    def test_form_handle_raises_exception(self):
        """
        The forms handle method should raise an improperly configured exception if the form is not bound
        """
        form = OmniFormBaseForm()
        self.assertRaises(ImproperlyConfigured, form.handle)

    def test_form_does_not_error_without_handlers(self):
        """
        The form should not error out if it doesn't have handlers
        """
        form = OmniFormBaseForm({})
        form.full_clean()
        form.handle()


class OmniModelFormBaseFormTestCase(TestCase):
    """
    Tests the OmniModelFormBaseForm
    """
    def test_extends_correct_classes(self):
        """
        The form class should extend the correct base classes
        """
        self.assertTrue(issubclass(OmniModelFormBaseForm, OmniFormBaseForm))
        self.assertTrue(issubclass(OmniModelFormBaseForm, forms.ModelForm))

    @patch('omniforms.forms.OmniModelFormBaseForm.handle')
    def test_save_calls_handle(self, patched_method):
        """
        The forms save method should call down to the handle method
        """
        class DummyForm(OmniModelFormBaseForm):
            class Meta(object):
                model = DummyModel
                exclude = ()

        form = DummyForm({
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
        form.save()
        patched_method.assert_called_once()


class EmailConfirmationHandlerBaseFormClassTestCase(TestCase):
    """
    Tests the EmailConfirmationHandlerBaseFormClass
    """
    class ConcreteEmailConfirmationHandlerForm(EmailConfirmationHandlerBaseFormClass):
        """
        Concrete model form class for testing purposes
        """
        class Meta:
            model = OmniFormEmailConfirmationHandler
            fields = '__all__'

    def setUp(self):
        super(EmailConfirmationHandlerBaseFormClassTestCase, self).setUp()
        self.form_1 = OmniFormFactory.create()
        self.email_field_1 = OmniEmailFieldFactory.create(form=self.form_1)
        self.form_2 = OmniFormFactory.create()
        self.email_field_2 = OmniEmailFieldFactory.create(form=self.form_2)

    def test_restricts_queryset(self):
        """
        The form should restrict the queryset to include only those fields which belong to the same form
        """
        form = self.ConcreteEmailConfirmationHandlerForm(
            instance=OmniFormEmailConfirmationHandler(form=self.form_1)
        )
        self.assertIn(self.email_field_1, form.fields['recipient_field'].queryset)
        self.assertNotIn(self.email_field_2, form.fields['recipient_field'].queryset)

    def test_shows_all_options_if_missing_instance(self):
        """
        The form should show all available email fields if the EmailConfirmationHandler instance is missing
        """
        form = self.ConcreteEmailConfirmationHandlerForm()
        self.assertIn(self.email_field_1, form.fields['recipient_field'].queryset)
        self.assertIn(self.email_field_2, form.fields['recipient_field'].queryset)

    def test_shows_all_options_if_instance_missing_form(self):
        """
        The form should show all available email fields if the EmailConfirmationHandler instance is missing its form
        """
        form = self.ConcreteEmailConfirmationHandlerForm(
            instance=OmniFormEmailConfirmationHandler()
        )
        self.assertIn(self.email_field_1, form.fields['recipient_field'].queryset)
        self.assertIn(self.email_field_2, form.fields['recipient_field'].queryset)
