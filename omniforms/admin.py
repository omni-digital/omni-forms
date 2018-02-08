# -*- coding: utf-8 -*-
"""
Admin for the omniforms app
"""
from __future__ import unicode_literals
from django.contrib import admin
from django.conf.urls import url
from django.contrib.contenttypes.admin import GenericTabularInline
from omniforms.admin_forms import OmniModelFormAdminForm
from omniforms.admin_views import OmniModelFormSelectFieldView, OmniModelFormCreateFieldView, OmniModelFormPreviewView
from omniforms.admin_views import OmniModelFormSelectHandlerView, OmniModelFormCreateHandlerView
from omniforms.admin_views import OmniModelFormUpdateFieldView, OmniModelFormUpdateHandlerView
from omniforms.admin_views import OmniFormSelectFieldView, OmniFormCreateFieldView, OmniFormUpdateFieldView
from omniforms.admin_views import OmniFormPreviewView, OmniFormSelectHandlerView, OmniFormCreateHandlerView
from omniforms.admin_views import OmniFormUpdateHandlerView
from omniforms.models import OmniForm, OmniModelForm, OmniField, OmniFormHandler


class OmniRelatedInlineAdmin(GenericTabularInline):
    """
    Admin class for handling related inline items for omniforms
    """
    extra = 0
    max_num = 0
    fields = ('name', 'order',)
    readonly_fields = ('name',)
    show_change_link = True
    template = 'admin/omniforms/base/inlines/omni_form_related_inline.html'


class OmniFieldAdmin(OmniRelatedInlineAdmin):
    """
    Generic admin for OmniField models
    """
    model = OmniField


class OmniHandlerAdmin(OmniRelatedInlineAdmin):
    """
    Generic admin for OmniFormHandler models
    """
    model = OmniFormHandler


class OmniModelFormAdmin(admin.ModelAdmin):
    """
    Admin class for OmniModelForm model instances
    """
    inlines = [OmniFieldAdmin, OmniHandlerAdmin]
    form = OmniModelFormAdminForm

    def get_readonly_fields(self, request, obj=None):
        """
        Method for getting readonly fields for the admin class form
        Content Type can only be set at the point of creation so make it
        readonly if we're editing a persisted model instance

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param obj: Model instance
        :type obj: omniforms.models.OmniModelForm

        :return: tuple of readonly field names
        """
        readonly_fields = super(OmniModelFormAdmin, self).get_readonly_fields(request, obj=obj)
        if obj and obj.pk:
            readonly_fields += ('content_type',)
        return readonly_fields

    def get_urls(self):
        """
        Method for getting urls for the admin class
        Adds extra urls for managing fields on the OmniModelForm instance

        :return: list of urls
        """
        return [
            url(
                r'^(.+)/preview/$',
                self.admin_site.admin_view(OmniModelFormPreviewView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_preview'
            ),
            url(
                r'^(.+)/add-field/$',
                self.admin_site.admin_view(OmniModelFormSelectFieldView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_addfield'
            ),
            url(
                r'^(.+)/add-field/(.+)/$',
                self.admin_site.admin_view(OmniModelFormCreateFieldView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_createfield'
            ),
            url(
                r'^(.+)/update-field/(.+)/$',
                self.admin_site.admin_view(OmniModelFormUpdateFieldView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_updatefield'
            ),
            url(
                r'^(.+)/add-handler/$',
                self.admin_site.admin_view(OmniModelFormSelectHandlerView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_addhandler'
            ),
            url(
                r'^(.+)/add-handler/(.+)/$',
                self.admin_site.admin_view(OmniModelFormCreateHandlerView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_createhandler'
            ),
            url(
                r'^(.+)/update-handler/(.+)/$',
                self.admin_site.admin_view(OmniModelFormUpdateHandlerView.as_view(admin_site=self)),
                name='omniforms_omnimodelform_updatehandler'
            ),
        ] + super(OmniModelFormAdmin, self).get_urls()


admin.site.register(OmniModelForm, OmniModelFormAdmin)


class OmniFormAdmin(admin.ModelAdmin):
    """
    Admin class for OmniForm model instances
    """
    inlines = [OmniFieldAdmin, OmniHandlerAdmin]

    def get_urls(self):
        """
        Method for getting urls for the admin class
        Adds extra urls for managing fields on the OmniModelForm instance

        :return: list of urls
        """
        return [
            url(
                r'^(.+)/preview/$',
                self.admin_site.admin_view(OmniFormPreviewView.as_view(admin_site=self)),
                name='omniforms_omniform_preview'
            ),
            url(
                r'^(.+)/add-field/$',
                self.admin_site.admin_view(OmniFormSelectFieldView.as_view(admin_site=self)),
                name='omniforms_omniform_addfield'
            ),
            url(
                r'^(.+)/add-field/(.+)/$',
                self.admin_site.admin_view(OmniFormCreateFieldView.as_view(admin_site=self)),
                name='omniforms_omniform_createfield'
            ),
            url(
                r'^(.+)/update-field/(.+)/(.+)/$',
                self.admin_site.admin_view(OmniFormUpdateFieldView.as_view(admin_site=self)),
                name='omniforms_omniform_updatefield'
            ),
            url(
                r'^(.+)/add-handler/$',
                self.admin_site.admin_view(OmniFormSelectHandlerView.as_view(admin_site=self)),
                name='omniforms_omniform_addhandler'
            ),
            url(
                r'^(.+)/add-handler/(.+)/$',
                self.admin_site.admin_view(OmniFormCreateHandlerView.as_view(admin_site=self)),
                name='omniforms_omniform_createhandler'
            ),
            url(
                r'^(.+)/update-handler/(.+)/$',
                self.admin_site.admin_view(OmniFormUpdateHandlerView.as_view(admin_site=self)),
                name='omniforms_omniform_updatehandler'
            ),
        ] + super(OmniFormAdmin, self).get_urls()


admin.site.register(OmniForm, OmniFormAdmin)
