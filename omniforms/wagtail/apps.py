# -*- coding:utf8 -*-
"""
Wagtail omni forms app config
"""
from __future__ import unicode_literals

from django.apps import AppConfig


class WagtailOmniFormsConfig(AppConfig):
    """
    Custom app config for the omni forms wagtail wrapper app
    """
    name = 'omniforms.wagtail'
    verbose_name = 'wagtail_omni_forms'
