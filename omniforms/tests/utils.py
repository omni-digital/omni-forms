# -*- coding: utf-8 -*-
"""
Test stubs for the omniforms app
"""
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from omniforms.tests.factories import OmniModelFormFactory


class OmniFormTestCaseStub(TestCase):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniFormTestCaseStub, self).setUp()
        self.omni_form = OmniModelFormFactory.create()


class OmniFormAdminTestCaseStub(OmniFormTestCaseStub):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniFormAdminTestCaseStub, self).setUp()
        user_model = get_user_model()
        # Create a user
        self.user = user_model(username='test', email='test@example.com', is_staff=True)
        self.user.set_password('test1234')
        self.user.save()
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
        # Log the user in
        self.client.login(username='test', password='test1234')
