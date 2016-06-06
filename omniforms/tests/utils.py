# -*- coding: utf-8 -*-
"""
Test stubs for the omniforms app
"""
from __future__ import unicode_literals
from django.contrib.auth import get_user_model
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
        self.user = user_model(username='test', email='test@example.com', is_staff=True)
        self.user.set_password('test1234')
        self.user.save()
        self.client.login(username='test', password='test1234')
