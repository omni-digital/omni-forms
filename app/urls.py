# -*- coding: utf-8 -*-
"""
URLS for the omniforms app - Used in testing
"""
from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]
