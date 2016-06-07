# -*- coding: utf-8 -*-
"""
Tests for the omniforms admin
"""
from __future__ import unicode_literals
from django.contrib.admin import ModelAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.core.urlresolvers import reverse, resolve
from django.test import TestCase
from omniforms.admin import OmniFieldAdmin, OmniModelFormAdmin, OmniHandlerAdmin
from omniforms.models import OmniField, OmniFormHandler
from omniforms.tests.utils import OmniFormTestCaseStub


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


class OmniModelFormAdminTestCase(OmniFormTestCaseStub):
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

    def test_add_field_view(self):
        """
        The class should add custom urls for adding a field
        """
        resolved = resolve(reverse('admin:omniforms_omnimodelform_addfield', args=[self.omni_form.pk]))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormAddFieldView')

    def test_create_field_view(self):
        """
        The class should add custom urls for creating a field
        """
        resolved = resolve(reverse('admin:omniforms_omnimodelform_createfield', args=[self.omni_form.pk, 'title']))
        self.assertEqual(resolved[0].__name__, 'OmniModelFormCreateFieldView')
