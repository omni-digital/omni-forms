# -*- coding: utf-8 -*-
"""
Admin for the omniforms app
"""
from __future__ import unicode_literals
from django.contrib import admin
from django.conf.urls import url
from django.contrib.contenttypes.admin import GenericTabularInline
from omniforms.admin_views import OmniModelFormAddFieldView, OmniModelFormCreateFieldView
from omniforms.models import OmniModelForm, OmniField


class OmniFieldAdmin(GenericTabularInline):
    """
    Generic admin for OmniField models
    """
    model = OmniField
    extra = 0
    max_num = 0
    fields = ('order',)


class OmniModelFormAdmin(admin.ModelAdmin):
    """
    Admin class for OmniModelForm model instances
    """
    inlines = [OmniFieldAdmin]

    def get_urls(self):
        """
        Method for getting urls for the admin class
        Adds extra urls for managing fields on the OmniModelForm instance

        :return: list of urls
        """
        return [
            url(
                r'^(.+)/add-field/$',
                self.admin_site.admin_view(OmniModelFormAddFieldView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_addfield'
            ),
            url(
                r'^(.+)/add-field/(.+)/$',
                self.admin_site.admin_view(OmniModelFormCreateFieldView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_createfield'
            ),
        ] + super(OmniModelFormAdmin, self).get_urls()


admin.site.register(OmniModelForm, OmniModelFormAdmin)
