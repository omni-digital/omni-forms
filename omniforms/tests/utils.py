# -*- coding: utf-8 -*-
"""
Test stubs for the omniforms app
"""
from __future__ import unicode_literals
from django.test import TestCase
from omniforms.tests.factories import OmniModelFormFactory


class OmniFormTestCaseStub(TestCase):
    """
    Test Stub for the omniforms app
    """
    def setUp(self):
        super(OmniFormTestCaseStub, self).setUp()
        self.omni_form = OmniModelFormFactory.create()
