# -*- coding: utf-8 -*-
"""
Tests for the omniforms admin
"""
from __future__ import unicode_literals

from django.contrib.admin import ModelAdmin
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.urlresolvers import reverse, resolve
from django.test import TestCase, RequestFactory
from mock import Mock

from omniforms.admin import OmniFieldAdmin, OmniFormAdmin, OmniModelFormAdmin, OmniHandlerAdmin
from omniforms.models import OmniField, OmniFormHandler, OmniModelForm, OmniFormEmailHandler
from omniforms.tests.factories import OmniModelFormFactory, OmniCharFieldFactory, OmniFormEmailHandlerFactory
from omniforms.tests.utils import OmniModelFormTestCaseStub, OmniBasicFormTestCaseStub


class OmniFieldAdminTestCase(TestCase):
    """
    Tests the OmniFieldAdmin
    """
    def test_extends_generic_tabular_inline(self):
        """
        The OmniFieldAdmin class should extend GenericTabularInline
        """
        self.assertTrue(issubclass(OmniFieldAdmin, GenericTabularInline))

    def test_model(self):
        """
        The OmniFieldAdmin class should use the correct model
        """
        self.assertEqual(OmniFieldAdmin.model, OmniField)

    def test_extra(self):
        """
        The OmniFieldAdmin class should not allow extra fields to be added
        """
        self.assertEqual(OmniFieldAdmin.extra, 0)

    def test_max_num(self):
        """
        The OmniFieldAdmin class should use set max_num = 0
        """
        self.assertEqual(OmniFieldAdmin.max_num, 0)

    def test_fields(self):
        """
        The OmniFieldAdmin class should define the correct model fields
        """
        self.assertIn('name', OmniFieldAdmin.fields)
        self.assertIn('order', OmniFieldAdmin.fields)

    def test_readonly_fields(self):
        """
        The OmniFieldAdmin class should define the correct readonly_fields
        """
        self.assertIn('name', OmniFieldAdmin.readonly_fields)


class OmniHandlerAdminTestCase(TestCase):
    """
    Tests the OmniHandlerAdmin
    """
    def test_extends_generic_tabular_inline(self):
        """
        The OmniHandlerAdmin class should extend GenericTabularInline
        """
        self.assertTrue(issubclass(OmniHandlerAdmin, GenericTabularInline))

    def test_model(self):
        """
        The OmniHandlerAdmin class should use the correct model
        """
        self.assertEqual(OmniHandlerAdmin.model, OmniFormHandler)

    def test_extra(self):
        """
        The OmniHandlerAdmin class should not allow extra fields to be added
        """
        self.assertEqual(OmniHandlerAdmin.extra, 0)

    def test_max_num(self):
        """
        The OmniHandlerAdmin class should use set max_num = 0
        """
        self.assertEqual(OmniHandlerAdmin.max_num, 0)

    def test_fields(self):
        """
        The OmniHandlerAdmin class should define the correct model fields
        """
        self.assertIn('name', OmniHandlerAdmin.fields)
        self.assertIn('order', OmniHandlerAdmin.fields)

    def test_readonly_fields(self):
        """
        The OmniHandlerAdmin class should define the correct readonly_fields
        """
        self.assertIn('name', OmniHandlerAdmin.readonly_fields)


class OmniModelFormAdminTestCase(OmniModelFormTestCaseStub):
    """
    Tests the OmniModelFormAdmin
    """
    def test_extends_model_admin(self):
        """
        The class should extend django.contrib.admin.ModelAdmin
        """
        self.assertTrue(issubclass(OmniModelFormAdmin, ModelAdmin))

    def test_omni_field_admin_inline(self):
        """
        The class should use the OmniFieldAdmin inline
        """
        self.assertIn(OmniFieldAdmin, OmniModelFormAdmin.inlines)
        self.assertIn(OmniHandlerAdmin, OmniModelFormAdmin.inlines)

    def test_preview_view(self):
        """
        The class should add custom urls for previewing the form
        """
        resolved = resolve(reverse('admin:omniforms_omnimodelform_preview', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormPreviewView')

    def test_add_field_view(self):
        """
        The class should add custom urls for adding a field
        """
        resolved = resolve(reverse('admin:omniforms_omnimodelform_addfield', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormSelectFieldView')

    def test_create_field_view(self):
        """
        The class should add custom urls for creating a field
        """
        resolved = resolve(reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title']))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormCreateFieldView')

    def test_update_field_view(self):
        """
        The class should add custom urls for updating a field
        """
        field = OmniCharFieldFactory.create(form=self.omni_form)
        resolved = resolve(reverse(
            'admin:omniforms_omnimodelform_updatefield',
            args=[field.object_id, field.name])
        )
        self.assertEqual(resolved[0].__name__, 'OmniModelFormUpdateFieldView')

    def test_add_handler_view(self):
        """
        The class should add custom urls for adding a handler
        """
        resolved = resolve(reverse('admin:omniforms_omnimodelform_addhandler', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormSelectHandlerView')

    def test_create_handler_view(self):
        """
        The class should add custom urls for creating a handler
        """
        content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        resolved = resolve(reverse(
            'admin:omniforms_omnimodelform_createhandler',
            args=[self.omni_form.pk, content_type.pk]
        ))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormCreateHandlerView')

    def test_update_handler_view(self):
        """
        The class should add custom urls for updating a handler
        """
        handler = OmniFormEmailHandlerFactory.create(form=self.omni_form)
        resolved = resolve(reverse(
            'admin:omniforms_omnimodelform_updatehandler',
            args=[handler.object_id, handler.pk])
        )
        self.assertEqual(resolved[0].__name__, 'OmniModelFormUpdateHandlerView')

    def test_get_readonly_fields_with_new_instance(self):
        """
        The content_type field should not be readonly when adding a new instance
        """
        request = RequestFactory().get('/fake-path/')
        instance = OmniModelForm()
        admin_instance = OmniModelFormAdmin(OmniModelForm, Mock())
        readonly_fields = admin_instance.get_readonly_fields(request)
        self.assertNotIn('content_type', readonly_fields)
        readonly_fields = admin_instance.get_readonly_fields(request, obj=instance)
        self.assertNotIn('content_type', readonly_fields)

    def test_get_readonly_fields_with_existing_instance(self):
        """
        The content_type field should be readonly when editing an existing instance
        """
        request = RequestFactory().get('/fake-path/')
        instance = OmniModelFormFactory.create()
        admin_instance = OmniModelFormAdmin(OmniModelForm, Mock())
        readonly_fields = admin_instance.get_readonly_fields(request, obj=instance)
        self.assertIn('content_type', readonly_fields)


class OmniBasicFormAdminTestCase(OmniBasicFormTestCaseStub):
    """
    Tests the OmniFormAdmin
    """
    def test_extends_model_admin(self):
        """
        The class should extend django.contrib.admin.ModelAdmin
        """
        self.assertTrue(issubclass(OmniFormAdmin, ModelAdmin))

    def test_omni_field_admin_inline(self):
        """
        The class should use the OmniFieldAdmin inline
        """
        self.assertIn(OmniFieldAdmin, OmniFormAdmin.inlines)
        self.assertIn(OmniHandlerAdmin, OmniFormAdmin.inlines)

    def test_preview_view(self):
        """
        The class should add custom urls for previewing the form
        """
        resolved = resolve(reverse('admin:omniforms_omniform_preview', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniFormPreviewView')

    def test_add_field_view(self):
        """
        The class should add custom urls for adding a field
        """
        resolved = resolve(reverse('admin:omniforms_omniform_addfield', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniFormSelectFieldView')

    def test_create_field_view(self):
        """
        The class should add custom urls for creating a field
        """
        resolved = resolve(reverse('admin:omniforms_omniform_createfield', args=[self.omni_form.pk, 'title']))
        self.assertEqual(resolved[0].__name__, 'OmniFormCreateFieldView')

    def test_update_field_view(self):
        """
        The class should add custom urls for updating a field
        """
        field = OmniCharFieldFactory.create(form=self.omni_form)
        resolved = resolve(reverse(
            'admin:omniforms_omniform_updatefield',
            args=[self.omni_form.pk, field.real_type_id, 'title'])
        )
        self.assertEqual(resolved[0].__name__, 'OmniFormUpdateFieldView')

    def test_add_handler_view(self):
        """
        The class should add custom urls for adding a handler
        """
        resolved = resolve(reverse('admin:omniforms_omniform_addhandler', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniFormSelectHandlerView')

    def test_create_handler_view(self):
        """
        The class should add custom urls for creating a handler
        """
        content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        resolved = resolve(reverse(
            'admin:omniforms_omniform_createhandler',
            args=[self.omni_form.pk, content_type.pk]
        ))
        self.assertEqual(resolved[0].__name__, 'OmniFormCreateHandlerView')

    def test_update_handler_view(self):
        """
        The class should add custom urls for updating a handler
        """
        handler = OmniFormEmailHandlerFactory.create(form=self.omni_form)
        resolved = resolve(reverse(
            'admin:omniforms_omniform_updatehandler',
            args=[handler.object_id, handler.pk])
        )
        self.assertEqual(resolved[0].__name__, 'OmniFormUpdateHandlerView')
