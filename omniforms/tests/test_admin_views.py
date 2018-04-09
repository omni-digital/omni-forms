# -*- coding: utf-8 -*-
"""
Tests the omniforms admin views
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from mock import patch
from omniforms.admin_forms import AddRelatedForm, FieldForm
from omniforms.admin_views import (
    OmniModelFormSelectFieldView,
    OmniModelFormCreateFieldView,
    OmniModelFormUpdateFieldView,
    OmniModelFormSelectHandlerView,
    OmniModelFormCreateHandlerView,
    OmniModelFormUpdateHandlerView,
    OmniFormSelectFieldView,
    OmniFormCreateFieldView,
    OmniFormUpdateFieldView,
    OmniFormSelectHandlerView,
    OmniFormCreateHandlerView,
    OmniFormUpdateHandlerView
)
from omniforms.models import (
    OmniForm,
    OmniModelForm,
    OmniField,
    OmniCharField,
    OmniBooleanField,
    OmniFloatField,
    OmniDateField,
    OmniDateTimeField,
    OmniDecimalField,
    OmniEmailField,
    OmniIntegerField,
    OmniTimeField,
    OmniUrlField,
    OmniFormHandler,
    OmniFormEmailHandler,
    OmniFormSaveInstanceHandler
)
from omniforms.tests.utils import OmniModelFormAdminTestCaseStub, OmniBasicFormAdminTestCaseStub
from omniforms.tests.factories import OmniCharFieldFactory, OmniFormEmailHandlerFactory


class OmniModelFormSelectFieldViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormSelectFieldView
    """
    def setUp(self):
        super(OmniModelFormSelectFieldViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omnimodelform_addfield', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['view'], OmniModelFormSelectFieldView)
        self.assertIsInstance(response.context['form'], AddRelatedForm)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertTemplateUsed(response, "admin/omniforms/base/selectfield_form.html")

    def test_forms_model_fields_choices(self):
        """
        The forms model_fields.choices should be constructed properly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIn(('title', 'title'), form.fields['choices'].choices)
        self.assertIn(('agree', 'agree'), form.fields['choices'].choices)
        self.assertIn(('some_date', 'some date'), form.fields['choices'].choices)
        self.assertIn(('some_datetime', 'some datetime'), form.fields['choices'].choices)
        self.assertIn(('some_decimal', 'some decimal'), form.fields['choices'].choices)
        self.assertIn(('some_email', 'some email'), form.fields['choices'].choices)
        self.assertIn(('some_float', 'some float'), form.fields['choices'].choices)
        self.assertIn(('some_integer', 'some integer'), form.fields['choices'].choices)
        self.assertIn(('some_time', 'some time'), form.fields['choices'].choices)
        self.assertIn(('some_url', 'some url'), form.fields['choices'].choices)

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
        response = self.client.post(self.url, data={'choices': 'title'}, follow=True)
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


class OmniModelFormCreateFieldViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormSelectFieldView
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
        self.assertTemplateUsed(response, 'admin/omniforms/base/field_form.html')
        self.assertIsInstance(response.context['view'], OmniModelFormCreateFieldView)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertEqual(response.context['model_field_name'], 'title')
        self.assertIsInstance(response.context['form'], FieldForm)

    def test_raises_404_for_invalid_omni_form(self):
        """
        The view should raise an HTTP 404 response if the omni form does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[9999, 'title'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_for_many_to_many_rel_field(self):
        """
        The view should raise an HTTP 404 response if the omni form does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'dummymodel3_set'])
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


class OmniModelFormUpdateFieldViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormUpdateFieldView
    """
    def setUp(self):
        super(OmniModelFormUpdateFieldViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
        self.field = OmniCharField(
            name='title',
            label='Title',
            widget_class='django.forms.widgets.TextInput',
            order=0,
            form=self.omni_form
        )
        self.field.save()
        self.form_data = {
            'id': self.field.pk,
            'required': False,
            'name': 'some_date',
            'label': 'Enter a date',
            'help_text': 'This will be used for something',
            'widget_class': OmniCharField.FORM_WIDGETS[0],
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'order': 0
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/field_form.html')
        self.assertIsInstance(response.context['view'], OmniModelFormUpdateFieldView)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertEqual(response.context['model_field_name'], 'title')
        self.assertIsInstance(response.context['form'], FieldForm)

    def test_raises_404_for_invalid_omni_form(self):
        """
        The view should raise an HTTP 404 response if the omni form does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[9999, 'title'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_for_invalid_field_name(self):
        """
        The view should raise an HTTP 404 response if the specified field does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'thisisnotafield'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_model_set_correctly(self):
        """
        The view should use the appropriate model for the field
        """
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertEqual(response.context['view'].model, OmniCharField)

    def test_required_field_widget_required(self):
        """
        The form should use a hidden widget for the required field if the corresponding model field is required
        """
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertIsInstance(response.context['form'].fields['required'].widget, forms.HiddenInput)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the name, widget_class, content_type and object_id fields
        """
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
        response = self.client.get(url)
        self.assertIsInstance(response.context['form'].fields['name'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
        response = self.client.post(url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
        response = self.client.post(url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_addfield', args=[self.omni_form.pk]))

    def test_invalid_widget_class(self):
        """
        It should not be possible to submit an invalid widget class in the form
        """
        self.form_data.update({'widget_class': 'django.forms.fields.DateField'})
        url = reverse('admin:omniforms_omnimodelform_updatefield', args=[self.omni_form.pk, 'title'])
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
        The view should require the omniforms.change_omnifield permission
        """
        self.user.user_permissions.remove(self.change_field_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))


class OmniModelFormPreviewViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormPreviewView
    """
    def setUp(self):
        super(OmniModelFormPreviewViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omnimodelform_preview', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/preview.html')
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertEqual(response.context['form'].__class__.__name__, self.omni_form.get_form_class().__name__)

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


class OmniModelFormSelectHandlerViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormSelectHandlerView
    """
    def setUp(self):
        super(OmniModelFormSelectHandlerViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omnimodelform_addhandler', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['view'], OmniModelFormSelectHandlerView)
        self.assertIsInstance(response.context['form'], AddRelatedForm)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertTemplateUsed(response, "admin/omniforms/base/selecthandler_form.html")

    def test_forms_model_fields_choices(self):
        """
        The forms choices.queryset should be constructed properly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        for content_type_id, content_type_name in form.fields['choices'].choices:
            content_type = ContentType.objects.get(pk=content_type_id)
            self.assertTrue(
                issubclass(content_type.model_class(), OmniFormHandler) and
                content_type.model_class() != OmniFormHandler
            )

    def test_raises_404(self):
        """
        The view should raise an HTTP 404 if the omni_form does not exist
        """
        response = self.client.get(reverse('admin:omniforms_omnimodelform_addhandler', args=[999999999]))
        self.assertEqual(response.status_code, 404)

    def test_redirects_to_create_handler_view(self):
        """
        The view should redirect to the CreateHandler view on successful form submission
        """
        content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        response = self.client.post(self.url, data={'choices': content_type.pk}, follow=True)
        expected_url = reverse('admin:omniforms_omnimodelform_createhandler', args=[self.omni_form.pk, content_type.pk])
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
        self.user.user_permissions.remove(self.add_handler_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))

    def test_get_form_choices(self):
        """
        The _get_form_choices method of the view should return content types that are OmniFormHandler subclasses
        """
        choices = OmniModelFormSelectHandlerView()._get_form_choices()
        email_handler_ctype = ContentType.objects.get_for_model(OmniFormEmailHandler)
        save_instance_handler_ctype = ContentType.objects.get_for_model(OmniFormSaveInstanceHandler)
        self.assertIn((email_handler_ctype.pk, '{0}'.format(email_handler_ctype)), choices)
        self.assertIn((save_instance_handler_ctype.pk, '{0}'.format(save_instance_handler_ctype)), choices)

    @patch('omniforms.models.ContentType.model_class')
    def test_get_form_choices_does_not_fail_if_model_class_is_none(self, patched_method):
        """
        The _get_form_choices method of the view should not raise an exception if the model class could not be resolved
        """
        patched_method.return_value = None
        OmniModelFormSelectHandlerView()._get_form_choices()


class OmniModelFormCreateHandlerViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormCreateHandlerView
    """
    def setUp(self):
        super(OmniModelFormCreateHandlerViewTestCase, self).setUp()
        self.content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        self.url = reverse(
            'admin:omniforms_omnimodelform_createhandler',
            args=[self.omni_form.pk, self.content_type.pk]
        )
        self.form_data = {
            'name': 'some_date',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'subject': 'This is a test',
            'recipients': 'a@b.com',
            'template': 'Hi there {{ user }}'
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/handler_form.html')
        self.assertEqual(int(response.context['handler_content_type_id']), self.content_type.pk)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertIsInstance(response.context['view'], OmniModelFormCreateHandlerView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_raises_404_if_content_type_not_exists(self):
        """
        The view should raise an HTTP 404 response if the specified content type does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_createhandler', args=[self.omni_form.pk, 9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_instanciated_with_new_instance(self):
        """
        The create form should be instanciated with a new (unpersisted) model instance
        """
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIsNotNone(form.instance)
        self.assertEqual(form.instance.form, self.omni_form)

    def test_raises_404_if_content_type_invalid(self):
        """
        The view should raise an HTTP 404 response if the specified content type is not a subclass of OmniFormHandler
        """
        invalid_content_type = ContentType.objects.get_for_model(OmniCharField)
        url = reverse('admin:omniforms_omnimodelform_createhandler', args=[self.omni_form.pk, invalid_content_type.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_if_content_type_is_base_form_handler(self):
        """
        The view should raise an HTTP 404 response if the specified content type is the base OmniFormHandler
        """
        invalid_content_type = ContentType.objects.get_for_model(OmniFormHandler)
        url = reverse('admin:omniforms_omnimodelform_createhandler', args=[self.omni_form.pk, invalid_content_type.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the content_type and object_id fields
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_form_initial_data(self):
        """
        The forms initial data should be appropriate
        """
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(OmniModelForm).pk
        )

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
        The view should require the omniforms.add_omnihandler permission
        """
        self.user.user_permissions.remove(self.add_handler_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_addhandler', args=[self.omni_form.pk]))


class OmniModelFormUpdateHandlerViewTestCase(OmniModelFormAdminTestCaseStub):
    """
    Tests the OmniModelFormUpdateHandlerView
    """
    def setUp(self):
        super(OmniModelFormUpdateHandlerViewTestCase, self).setUp()
        self.instance = OmniFormEmailHandler(
            name='Send an email',
            order=0,
            content_type=ContentType.objects.get_for_model(self.omni_form),
            object_id=self.omni_form.pk,
            subject='This is a test',
            recipients='a@b.com',
            template='Hi there {{ user }}'
        )
        self.instance.save()
        self.url = reverse(
            'admin:omniforms_omnimodelform_updatehandler',
            args=[self.omni_form.pk, self.instance.pk]
        )
        self.form_data = {
            'name': 'Send an email',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'subject': 'This is a test',
            'recipients': 'a@b.com',
            'template': 'Hi there {{ user }}'
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/handler_form.html')
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertIsInstance(response.context['view'], OmniModelFormUpdateHandlerView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_raises_404_if_handler_not_exists(self):
        """
        The view should raise an HTTP 404 response if the specified handler does not exist
        """
        url = reverse('admin:omniforms_omnimodelform_updatehandler', args=[self.omni_form.pk, 9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the content_type and object_id fields
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_form_initial_data(self):
        """
        The forms initial data should be appropriate
        """
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(OmniModelForm).pk
        )

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
        The view should require the omniforms.change_omnihandler permission
        """
        self.user.user_permissions.remove(self.change_handler_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omnimodelform_addhandler', args=[self.omni_form.pk]))


class OmniFormSelectFieldViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormSelectFieldView
    """
    def setUp(self):
        super(OmniFormSelectFieldViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omniform_addfield', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['view'], OmniFormSelectFieldView)
        self.assertIsInstance(response.context['form'], AddRelatedForm)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertTemplateUsed(response, "admin/omniforms/base/selectfield_form.html")

    def test_forms_model_fields_choices(self):
        """
        The forms model_fields.choices should be constructed properly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        expected_choices = [
            [instance.pk, instance.name] for instance in ContentType.objects.order_by('model')
            if instance.model_class() is not None
            and issubclass(instance.model_class(), OmniField)
            and instance.model_class() != OmniField
        ]

        for expected_choice in expected_choices:
            self.assertIn(expected_choice, form.fields['choices'].choices)

    def test_raises_404(self):
        """
        The view should raise an HTTP 404 if the omni_form does not exist
        """
        response = self.client.get(reverse('admin:omniforms_omniform_addfield', args=[999999999]))
        self.assertEqual(response.status_code, 404)

    def test_redirects_to_create_field_view(self):
        """
        The view should redirect to the CreateField view on successful form submission
        """
        content_type = ContentType.objects.get_for_model(OmniCharField)
        response = self.client.post(self.url, data={'choices': content_type.pk}, follow=True)
        expected_url = reverse(
            'admin:omniforms_omniform_createfield',
            args=[self.omni_form.pk, content_type.pk]
        )
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


class OmniFormCreateFieldViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormSelectFieldView
    """
    def setUp(self):
        super(OmniFormCreateFieldViewTestCase, self).setUp()
        self.content_type = ContentType.objects.get_for_model(OmniDateField)
        self.url = reverse(
            'admin:omniforms_omniform_createfield',
            args=[self.omni_form.pk, self.content_type.pk]
        )
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
        self.assertTemplateUsed(response, 'admin/omniforms/base/field_form.html')
        self.assertIsInstance(response.context['view'], OmniFormCreateFieldView)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertIsInstance(response.context['form'], FieldForm)

    def test_raises_404_for_invalid_omni_form(self):
        """
        The view should raise an HTTP 404 response if the omni form does not exist
        """
        url = reverse('admin:omniforms_omniform_createfield', args=[9999, self.content_type.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_for_invalid_field_name(self):
        """
        The view should raise an HTTP 404 response if the specified field does not exist
        """
        url = reverse('admin:omniforms_omniform_createfield', args=[self.omni_form.pk, 99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the name, widget_class, content_type and object_id fields
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'].fields['widget_class'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_form_initial_data_title(self):
        """
        The forms initial data should be appropriate
        """
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(self.omni_form).pk
        )

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_addfield', args=[self.omni_form.pk]))

    def test_invalid_widget_class(self):
        """
        It should not be possible to submit an invalid widget class in the form
        """
        self.form_data.update({'widget_class': 'django.forms.fields.CharField'})
        response = self.client.post(self.url, self.form_data, follow=True)
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


class OmniFormUpdateFieldViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormUpdateFieldView
    """
    def setUp(self):
        super(OmniFormUpdateFieldViewTestCase, self).setUp()
        self.field = OmniCharFieldFactory.create(form=self.omni_form)
        self.url = reverse(
            'admin:omniforms_omniform_updatefield',
            args=[self.field.object_id, self.field.real_type_id, self.field.name]
        )
        self.form_data = {
            'id': self.field.pk,
            'required': False,
            'name': 'some_date',
            'label': 'Enter a date',
            'help_text': 'This will be used for something',
            'widget_class': OmniCharField.FORM_WIDGETS[0],
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'order': 0
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/field_form.html')
        self.assertIsInstance(response.context['view'], OmniFormUpdateFieldView)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertIsInstance(response.context['form'], FieldForm)

    def test_raises_404_for_invalid_omni_form(self):
        """
        The view should raise an HTTP 404 response if the omni form does not exist
        """
        url = reverse(
            'admin:omniforms_omniform_updatefield',
            args=[99999, self.field.real_type_id, self.field.name]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_for_invalid_field_name(self):
        """
        The view should raise an HTTP 404 response if the specified field does not exist
        """
        url = reverse(
            'admin:omniforms_omniform_updatefield',
            args=[self.field.object_id, self.field.real_type_id, 'thisisnotafield']
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_model_set_correctly(self):
        """
        The view should use the appropriate model for the field
        """
        response = self.client.get(self.url)
        self.assertEqual(response.context['view'].model, OmniCharField)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the content_type and object_id fields
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_addfield', args=[self.omni_form.pk]))

    def test_invalid_widget_class(self):
        """
        It should not be possible to submit an invalid widget class in the form
        """
        self.form_data.update({'widget_class': 'django.forms.fields.DateField'})
        response = self.client.post(self.url, self.form_data, follow=True)
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
        The view should require the omniforms.change_omnifield permission
        """
        self.user.user_permissions.remove(self.change_field_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))


class OmniFormPreviewViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormPreviewView
    """
    def setUp(self):
        super(OmniFormPreviewViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omniform_preview', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/preview.html')
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertEqual(response.context['form'].__class__.__name__, self.omni_form.get_form_class().__name__)

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


class OmniFormSelectHandlerViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormSelectHandlerView
    """
    def setUp(self):
        super(OmniFormSelectHandlerViewTestCase, self).setUp()
        self.url = reverse('admin:omniforms_omniform_addhandler', args=[self.omni_form.pk])

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['view'], OmniFormSelectHandlerView)
        self.assertIsInstance(response.context['form'], AddRelatedForm)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertTemplateUsed(response, "admin/omniforms/base/selecthandler_form.html")

    def test_forms_model_fields_choices(self):
        """
        The forms choices.queryset should be constructed properly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        for content_type_id, content_type_name in form.fields['choices'].choices:
            content_type = ContentType.objects.get(pk=content_type_id)
            self.assertTrue(
                issubclass(content_type.model_class(), OmniFormHandler) and
                content_type.model_class() != OmniFormHandler
            )

    def test_raises_404(self):
        """
        The view should raise an HTTP 404 if the omni_form does not exist
        """
        response = self.client.get(reverse('admin:omniforms_omniform_addhandler', args=[999999999]))
        self.assertEqual(response.status_code, 404)

    def test_redirects_to_create_handler_view(self):
        """
        The view should redirect to the CreateHandler view on successful form submission
        """
        content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        response = self.client.post(self.url, data={'choices': content_type.pk}, follow=True)
        expected_url = reverse('admin:omniforms_omniform_createhandler', args=[self.omni_form.pk, content_type.pk])
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
        self.user.user_permissions.remove(self.add_handler_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))

    def test_get_form_choices(self):
        """
        The _get_form_choices method of the view should return content types that are OmniFormHandler subclasses
        """
        choices = OmniFormSelectHandlerView()._get_form_choices()
        email_handler_ctype = ContentType.objects.get_for_model(OmniFormEmailHandler)
        save_instance_handler_ctype = ContentType.objects.get_for_model(OmniFormSaveInstanceHandler)
        self.assertIn((email_handler_ctype.pk, '{0}'.format(email_handler_ctype)), choices)
        self.assertIn((save_instance_handler_ctype.pk, '{0}'.format(save_instance_handler_ctype)), choices)

    @patch('omniforms.models.ContentType.model_class')
    def test_get_form_choices_does_not_fail_if_model_class_is_none(self, patched_method):
        """
        The _get_form_choices method of the view should not raise an exception if the model class could not be resolved
        """
        patched_method.return_value = None
        OmniModelFormSelectHandlerView()._get_form_choices()


class OmniFormCreateHandlerViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormCreateHandlerView
    """
    def setUp(self):
        super(OmniFormCreateHandlerViewTestCase, self).setUp()
        self.content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        self.url = reverse(
            'admin:omniforms_omniform_createhandler',
            args=[self.omni_form.pk, self.content_type.pk]
        )
        self.form_data = {
            'name': 'some_email',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'subject': 'This is a test',
            'recipients': 'a@b.com',
            'template': 'Hi there {{ user }}'
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/handler_form.html')
        self.assertEqual(int(response.context['handler_content_type_id']), self.content_type.pk)
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertIsInstance(response.context['view'], OmniFormCreateHandlerView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_raises_404_if_content_type_not_exists(self):
        """
        The view should raise an HTTP 404 response if the specified content type does not exist
        """
        url = reverse('admin:omniforms_omniform_createhandler', args=[self.omni_form.pk, 9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_instanciated_with_new_instance(self):
        """
        The create form should be instanciated with a new (unpersisted) model instance
        """
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIsNotNone(form.instance)
        self.assertEqual(form.instance.form, self.omni_form)

    def test_raises_404_if_content_type_invalid(self):
        """
        The view should raise an HTTP 404 response if the specified content type is not a subclass of OmniFormHandler
        """
        invalid_content_type = ContentType.objects.get_for_model(OmniCharField)
        url = reverse('admin:omniforms_omniform_createhandler', args=[self.omni_form.pk, invalid_content_type.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_raises_404_if_content_type_is_base_form_handler(self):
        """
        The view should raise an HTTP 404 response if the specified content type is the base OmniFormHandler
        """
        invalid_content_type = ContentType.objects.get_for_model(OmniFormHandler)
        url = reverse('admin:omniforms_omniform_createhandler', args=[self.omni_form.pk, invalid_content_type.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the content_type and object_id fields
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_form_initial_data(self):
        """
        The forms initial data should be appropriate
        """
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(OmniForm).pk
        )

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
        The view should require the omniforms.add_omnihandler permission
        """
        self.user.user_permissions.remove(self.add_handler_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_addhandler', args=[self.omni_form.pk]))


class OmniFormUpdateHandlerViewTestCase(OmniBasicFormAdminTestCaseStub):
    """
    Tests the OmniFormUpdateHandlerView
    """
    def setUp(self):
        super(OmniFormUpdateHandlerViewTestCase, self).setUp()
        self.instance = OmniFormEmailHandlerFactory.create(form=self.omni_form)
        self.url = reverse(
            'admin:omniforms_omniform_updatehandler',
            args=[self.omni_form.pk, self.instance.pk]
        )
        self.form_data = {
            'name': 'Send an email',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.omni_form).pk,
            'object_id': self.omni_form.pk,
            'subject': 'This is a test',
            'recipients': 'a@b.com',
            'template': 'Hi there {{ user }}'
        }

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admin/omniforms/base/handler_form.html')
        self.assertEqual(response.context['omni_form'], self.omni_form)
        self.assertIsInstance(response.context['view'], OmniFormUpdateHandlerView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_raises_404_if_handler_not_exists(self):
        """
        The view should raise an HTTP 404 response if the specified handler does not exist
        """
        url = reverse('admin:omniforms_omniform_updatehandler', args=[self.omni_form.pk, 9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_form_hidden_widgets(self):
        """
        The form should use hidden input widgets for the content_type and object_id fields
        """
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'].fields['content_type'].widget, forms.HiddenInput)
        self.assertIsInstance(response.context['form'].fields['object_id'].widget, forms.HiddenInput)

    def test_form_initial_data(self):
        """
        The forms initial data should be appropriate
        """
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['object_id'], self.omni_form.pk)
        self.assertEqual(
            response.context['form'].initial['content_type'],
            ContentType.objects.get_for_model(OmniForm).pk
        )

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
        The view should require the omniforms.change_omnihandler permission
        """
        self.user.user_permissions.remove(self.change_handler_permission)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))

    def test_redirects_to_change_form(self):
        """
        The view should redirect to the change form
        """
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_change', args=[self.omni_form.pk]))

    def test_redirects_to_add_form(self):
        """
        The view should redirect to the add form
        """
        self.form_data.update({'_addanother': 'Save and add another'})
        response = self.client.post(self.url, self.form_data, follow=True)
        self.assertRedirects(response, reverse('admin:omniforms_omniform_addhandler', args=[self.omni_form.pk]))
