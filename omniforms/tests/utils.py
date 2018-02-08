# -*- coding: utf-8 -*-
"""
Test stubs for the omniforms app
"""
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from omniforms.tests.factories import OmniFormFactory, OmniModelFormFactory


class UserTestCaseStub(TestCase):
    """
    Test stub for working with a user
    """
    def setUp(self):
        super(UserTestCaseStub, self).setUp()
        user_model = get_user_model()
        # Create a user
        self.user = user_model(username='test', email='test@example.com', is_staff=True)
        self.user.set_password('test1234')
        self.user.save()
        # Log the user in
        self.client.login(username='test', password='test1234')


class OmniModelFormTestCaseStub(UserTestCaseStub):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniModelFormTestCaseStub, self).setUp()
        self.omni_form = OmniModelFormFactory.create()


class OmniBasicFormTestCaseStub(UserTestCaseStub):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniBasicFormTestCaseStub, self).setUp()
        self.omni_form = OmniFormFactory.create()


class OmniModelFormAdminTestCaseStub(OmniModelFormTestCaseStub):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniModelFormAdminTestCaseStub, self).setUp()
        # Get model permissions
        self.add_field_permission = Permission.objects.get(codename='add_omnifield')
        self.change_field_permission = Permission.objects.get(codename='change_omnifield')
        self.add_form_permission = Permission.objects.get(codename='add_omnimodelform')
        self.change_form_permission = Permission.objects.get(codename='change_omnimodelform')
        self.add_handler_permission = Permission.objects.get(codename='add_omniformhandler')
        self.change_handler_permission = Permission.objects.get(codename='change_omniformhandler')
        # Assign model permissions
        self.user.user_permissions.add(self.add_field_permission)
        self.user.user_permissions.add(self.change_field_permission)
        self.user.user_permissions.add(self.add_form_permission)
        self.user.user_permissions.add(self.change_form_permission)
        self.user.user_permissions.add(self.add_handler_permission)
        self.user.user_permissions.add(self.change_handler_permission)


class OmniBasicFormAdminTestCaseStub(OmniBasicFormTestCaseStub):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniBasicFormAdminTestCaseStub, self).setUp()
        # Get model permissions
        self.add_field_permission = Permission.objects.get(codename='add_omnifield')
        self.change_field_permission = Permission.objects.get(codename='change_omnifield')
        self.add_form_permission = Permission.objects.get(codename='add_omniform')
        self.change_form_permission = Permission.objects.get(codename='change_omniform')
        self.add_handler_permission = Permission.objects.get(codename='add_omniformhandler')
        self.change_handler_permission = Permission.objects.get(codename='change_omniformhandler')
        # Assign model permissions
        self.user.user_permissions.add(self.add_field_permission)
        self.user.user_permissions.add(self.change_field_permission)
        self.user.user_permissions.add(self.add_form_permission)
        self.user.user_permissions.add(self.change_form_permission)
        self.user.user_permissions.add(self.add_handler_permission)
        self.user.user_permissions.add(self.change_handler_permission)
