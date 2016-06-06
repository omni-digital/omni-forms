# -*- coding: utf-8 -*-
"""
Tests the omniforms admin views
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from omniforms.admin_forms import OmniModelFormAddFieldForm, OmniModelFormCreateFieldForm
from omniforms.admin_views import OmniModelFormAddFieldView, OmniModelFormCreateFieldView
from omniforms.models import (
    OmniModelForm,
    OmniCharField,
    OmniBooleanField,
    OmniFloatField,
    OmniDateField,
    OmniDateTimeField,
    OmniDecimalField,
    OmniEmailField,
    OmniIntegerField,
    OmniTimeField,
    OmniUrlField
)
from omniforms.tests.utils import OmniFormAdminTestCaseStub


class OmniModelFormAddFieldViewTestCase(OmniFormAdminTestCaseStub):
    """
    Tests the OmniModelFormAddFieldView
    """
    def setUp(self):
        super(OmniModelFormAddFieldViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omnimodelform_addfield', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['view'], OmniModelFormAddFieldView)
        self.assertIsInstance(response.context['form'], OmniModelFormAddFieldForm)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertTemplateUsed(response, "admin/omniforms/omnimodelform/addfield_form.html")

    def test_forms_model_fields_choices(self):
        """
        The forms model_fields.choices should be constructed properly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIn(('title', 'title'), form.fields['model_field'].choices)
        self.assertIn(('agree', 'agree'), form.fields['model_field'].choices)
        self.assertIn(('some_date', 'some date'), form.fields['model_field'].choices)
        self.assertIn(('some_datetime', 'some datetime'), form.fields['model_field'].choices)
        self.assertIn(('some_decimal', 'some decimal'), form.fields['model_field'].choices)
        self.assertIn(('some_email', 'some email'), form.fields['model_field'].choices)
        self.assertIn(('some_float', 'some float'), form.fields['model_field'].choices)
        self.assertIn(('some_integer', 'some integer'), form.fields['model_field'].choices)
        self.assertIn(('some_time', 'some time'), form.fields['model_field'].choices)
        self.assertIn(('some_url', 'some url'), form.fields['model_field'].choices)

    def test_raises_404(self):
        """
        The view should raise an HTTP 404 if the omni_form does not exist
        """
        response = self.client.get(reverse('admin:omniforms_omnimodelform_addfield', args=[999999999]))
        self.assertEqual(response.status_code, 404)

    def test_redirects_to_create_field_view(self):
        """
        The view should redirect to the CreateField view on successful form submission
        """
        response = self.client.post(self.url, data={'model_field': 'title'}, follow=True)
        expected_url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title'])
        self.assertRedirects(response, expected_url)

    def test_staff_required(self):
        """
        The view should not be accessible to non staff users
        """
        self.user.is_staff = False
        self.user.save()
        response = self.client.get(self.url, follow=True)
        redirect_url = '{0}?next={1}'.format(reverse('admin:login'), self.url)
        self.assertRedirects(response, redirect_url)

    def test_permission_required(self):
        """
        The view should require the omniforms.add_omnifield permission
        """
        self.user.user_permissions.remove(self.add_field_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))


class OmniModelFormCreateFieldViewTestCase(OmniFormAdminTestCaseStub):
    """
    Tests the OmniModelFormAddFieldView
    """
    def setUp(self):
        super(OmniModelFormCreateFieldViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title'])
        self.form_data = {
            'required': False,
            'name': 'some_date',
            'label': 'Enter a date',
            'help_text': 'This will be used for something',
            'widget_class': OmniDateField.FORM_WIDGETS[0],
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'order': 0
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/omnimodelform/createfield_form.html')
        self.assertIsInstance(response.context['view'], OmniModelFormCreateFieldView)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertEqual(response.context['model_field_name'], 'title')
        self.assertIsInstance(response.context['form'], OmniModelFormCreateFieldForm)

    def test_raises_404_for_invalid_omni_form(self):
        """
        The view should raise an HTTP 404 response if the omni form does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[9999, 'title'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_for_invalid_field_name(self):
        """
        The view should raise an HTTP 404 response if the specified field does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'thisisnotafield'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_if_field_already_specified(self):
        """
        The view should raise an HTTP 404 response if the specified field has already been used
        """
        instance = OmniCharField(
            name='title',
            label='title',
            required=False,
            widget_class=OmniCharField.FORM_WIDGETS[0],
            order=0,
            form=self.omni_form
        )
        instance.save()
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_model_set_correctly(self):
        """
        The view should use the appropriate model for the field
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniCharField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'agree'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniBooleanField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_float'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniFloatField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniDateField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_datetime'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniDateTimeField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_decimal'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniDecimalField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_email'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniEmailField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_integer'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniIntegerField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_time'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniTimeField)

        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_url'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniUrlField)

    def test_required_field_widget_required(self):
        """
        The form should use a hidden widget for the required field if the corresponding model field is required
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertIsInstance(response.context['form'].fields['required'].widget, forms.HiddenInput)

    def test_required_field_widget_optional(self):
        """
        The form should use a checkbox widget for the required field if the corresponding model field is optional
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.get(url)
        self.assertIsInstance(response.context['form'].fields['required'].widget, forms.CheckboxInput)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the name, widget_class, content_type and object_id fields
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.get(url)
        self.assertIsInstance(response.context['form'].fields['name'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['widget_class'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_form_initial_data_title(self):
        """
        The forms initial data should be appropriate
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertTrue(response.context['form'].initial['required'])
        self.assertEqual(response.context['form'].initial['widget_class'], OmniCharField.FORM_WIDGETS[0])
        self.assertEqual(response.context['form'].initial['label'], 'Title')
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(response.context['form'].initial['name'], 'title')
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(OmniModelForm).pk
        )

    def test_form_initial_data_some_date(self):
        """
        The forms initial data should be appropriate
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.get(url)
        self.assertFalse(response.context['form'].initial['required'])
        self.assertEqual(response.context['form'].initial['widget_class'], OmniDateField.FORM_WIDGETS[0])
        self.assertEqual(response.context['form'].initial['label'], 'Some date')
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(response.context['form'].initial['name'], 'some_date')
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(OmniModelForm).pk
        )

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.post(url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.post(url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_addfield', args=[self.omni_form.pk]))

    def test_invalid_widget_class(self):
        """
        It should not be possible to submit an invalid widget class in the form
        """
        self.form_data.update({'widget_class': 'django.forms.fields.CharField'})
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'some_date'])
        response = self.client.post(url, self.form_data, follow=True)
        self.assertIn('widget_class', response.context['form'].errors)

    def test_staff_required(self):
        """
        The view should not be accessible to non staff users
        """
        self.user.is_staff = False
        self.user.save()
        response = self.client.get(self.url, follow=True)
        redirect_url = '{0}?next={1}'.format(reverse('admin:login'), self.url)
        self.assertRedirects(response, redirect_url)

    def test_permission_required(self):
        """
        The view should require the omniforms.add_omnifield permission
        """
        self.user.user_permissions.remove(self.add_field_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))
