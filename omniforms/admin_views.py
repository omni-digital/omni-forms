# -*- coding: utf-8 -*-
"""
Admin views for the omniforms app
"""
from __future__ import unicode_literals
from braces.views import PermissionRequiredMixin
from django import forms
from django.contrib.admin.options import get_content_type_for_model, IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.core.urlresolvers import reverse
from django.forms import modelform_factory
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import FormView, CreateView, DetailView
from omniforms.admin_forms import OmniModelFormAddRelatedForm, OmniModelFormCreateFieldForm
from omniforms.models import OmniModelForm, OmniField, OmniRelatedField, OmniFormHandler


class AdminView(PermissionRequiredMixin, FormView):
    """
    Admin view mixin
    """
    admin_site = None

    def __init__(self, **kwargs):
        """
        Sets up attributes on the instance

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(AdminView, self).__init__(**kwargs)
        self.request = None

    def get_context_data(self, **kwargs):
        """
        Gets context data required for the admin view

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Dict of data for the admin template
        """
        context_data = super(AdminView, self).get_context_data(**kwargs)
        opts = self.admin_site.model._meta
        context_data.update({
            'add': False,
            'change': False,
            'has_add_permission': self.admin_site.has_add_permission(self.request),
            'has_change_permission': self.admin_site.has_change_permission(self.request),
            'has_delete_permission': self.admin_site.has_delete_permission(self.request),
            'has_absolute_url': False,
            'absolute_url': None,
            'opts': opts,
            'content_type_id': get_content_type_for_model(self.admin_site.model).pk,
            'save_as': self.admin_site.save_as,
            'save_on_top': self.admin_site.save_on_top,
            'to_field_var': TO_FIELD_VAR,
            'is_popup_var': IS_POPUP_VAR,
            'is_popup': False,
            'app_label': opts.app_label,
        })
        return context_data


class OmniFormAdminView(AdminView):
    """
    Admin view for working with omni forms
    """
    def __init__(self, **kwargs):
        """
        Sets up attributes required for the view

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniFormAdminView, self).__init__(**kwargs)
        self.omni_form = None

    @staticmethod
    def _load_omni_form(pk):
        """
        Loads the omin form instance from the database or raises an HTTP 404

        :param pk: The id of the omni form instance
        :type pk: int

        :return: OmniForm model instance
        """
        return get_object_or_404(OmniModelForm, pk=pk)

    def dispatch(self, request, *args, **kwargs):
        """
        Custom dispatch method
        Loads the form that the field is being added to before calling super

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Http Response
        """
        self.omni_form = self._load_omni_form(args[0])
        return super(OmniFormAdminView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Custom implementation of get_context_data
        Adds data to the context required by the admin view

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Dict of context data for rendering the template
        """
        context_data = super(OmniFormAdminView, self).get_context_data(**kwargs)
        context_data.update({
            'omni_form': self.omni_form,
            'has_change_permission': self.admin_site.has_change_permission(self.request, self.omni_form),
            'has_delete_permission': self.admin_site.has_delete_permission(self.request, self.omni_form),
        })
        return context_data


class OmniModelFormAddRelatedView(OmniFormAdminView):
    """
    View for adding a related model to the Omni Model Form instance in the django admin
    """
    form_class = None
    template_name = None
    permission_required = None
    url_name = None

    def _get_form_choices(self):
        """
        Method for getting choices for the form instance

        :raises: NotImplementedError
        """
        raise NotImplementedError('\'{0}\' must implement its own _get_form_choices '
                                  'method'.format(self.__class__.__name__))

    def get_form_kwargs(self):
        """
        Custom implementation of get_form_kwargs
        Adds a list of model fields to the kwargs for use in the form

        :return: Dict of kwargs for the form
        """
        form_kwargs = super(OmniModelFormAddRelatedView, self).get_form_kwargs()
        form_kwargs['choices'] = self._get_form_choices()
        return form_kwargs

    def form_valid(self, form):
        """
        Called when the submitted form is valid

        :param form: Valid form instance
        :type form: omniforms.admin_forms.OmniModelFormAddRelatedForm

        :return: Http Response
        """
        url = reverse(self.url_name, args=(self.omni_form.pk, form.cleaned_data['choices']))
        return HttpResponseRedirect(url)


class OmniModelFormAddFieldView(OmniModelFormAddRelatedView):
    """
    View for adding a field to the Omni Model Form instance in the django admin
    """
    form_class = OmniModelFormAddRelatedForm
    template_name = "admin/omniforms/omnimodelform/addfield_form.html"
    permission_required = "omniforms.add_omnifield"
    url_name = 'admin:omniforms_omnimodelform_createfield'

    def _get_form_choices(self):
        """
        Custom implementation of get_form_kwargs
        Adds a list of model fields to the kwargs for use in the form

        :return: Dict of kwargs for the form
        """
        return self.omni_form.get_model_field_choices()


class OmniModelFormAddHandlerView(OmniModelFormAddRelatedView):
    """
    View for adding a handler to the Omni Model Form instance in the django admin
    """
    form_class = OmniModelFormAddRelatedForm
    template_name = "admin/omniforms/omnimodelform/addhandler_form.html"
    permission_required = "omniforms.add_omniformhandler"
    url_name = 'admin:omniforms_omnimodelform_createhandler'

    def _get_form_choices(self):
        """
        Method for getting form handler model class content types

        :return: Queryset of ContentType model instances
        """
        content_types = filter(
            lambda x: (
                x.model_class() is not None and
                issubclass(x.model_class(), OmniFormHandler) and
                x.model_class() != OmniFormHandler
            ),
            ContentType.objects.all()
        )
        return [(content_type.pk, '{0}'.format(content_type)) for content_type in content_types]


class OmniModelFormCreateRelatedView(OmniFormAdminView, CreateView):
    """
    Base view class for creating OmniForm related objects
    """
    form_class = forms.ModelForm
    add_another_url_name = 'admin:omniforms_omnimodelform_addfield'
    exclude = ('id', 'real_type')

    def get_initial(self):
        """
        Gets initial data for the form

        :return: Dict of initial data
        """
        initial = super(OmniModelFormCreateRelatedView, self).get_initial()
        initial['content_type'] = ContentType.objects.get_for_model(self.omni_form).pk
        initial['object_id'] = self.omni_form.pk
        return initial

    def _get_form_widgets(self):
        """
        Returns a dict of form widgets keyed by field name

        :return: Dict of field widgets
        """
        return {
            'object_id': forms.HiddenInput,
            'content_type': forms.HiddenInput,
        }

    def get_form_class(self):
        """
        Method for generating a form class for the view

        :return: ModelForm class
        """
        return modelform_factory(
            self.model,
            exclude=self.exclude,
            form=self.form_class,
            widgets=self._get_form_widgets()
        )

    def get_success_url(self):
        """
        Method for getting the success URL to redirect the user to on successful form submission

        :return: Url to redirect the user to
        """
        if '_addanother' in self.request.POST:
            return reverse(self.add_another_url_name, args=[self.omni_form.pk])
        else:
            return reverse('admin:omniforms_omnimodelform_change', args=[self.omni_form.pk])


class OmniModelFormCreateFieldView(OmniModelFormCreateRelatedView):
    """
    Creates a form field for the specified form
    """
    template_name = 'admin/omniforms/omnimodelform/createfield_form.html'
    permission_required = "omniforms.add_omnifield"
    form_class = OmniModelFormCreateFieldForm

    def __init__(self, *args, **kwargs):
        """
        Sets up attributes required for the view

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniModelFormCreateFieldView, self).__init__(*args, **kwargs)
        self.model_field = None
        self.model_field_name = None

    def dispatch(self, request, *args, **kwargs):
        """
        Custom dispatch method
        Gets the omni form instance and sets the model for the view

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param request: Http Request instance
        :type request: django.http.HttpRequest
        """
        omni_form_id = args[0]
        model_field_name = args[1]

        self.omni_form = self._load_omni_form(omni_form_id)

        if model_field_name not in self.omni_form.get_model_field_names():
            raise Http404

        if model_field_name in self.omni_form.used_field_names:
            raise Http404

        self.model = OmniField.get_concrete_class_for_model_field(self.model_field)
        return super(OmniModelFormCreateFieldView, self).dispatch(request, *args, **kwargs)

    def _get_form_widgets(self):
        """
        Returns a dict of form widgets keyed by field name

        :return: Dict of field widgets
        """
        widgets = super(OmniModelFormCreateFieldView, self)._get_form_widgets()
        widgets.update({
            'name': forms.HiddenInput,
            'widget_class': forms.HiddenInput,
        })

        if self._field_is_required:
            widgets['required'] = forms.HiddenInput

        if issubclass(self.model, OmniRelatedField):
            widgets['related_type'] = forms.HiddenInput

        if len(self.model.FORM_WIDGETS) > 1:
            choices = map(lambda x: (x, x.rsplit('.')[-1]), self.model.FORM_WIDGETS)
            widgets['widget_class'] = forms.Select(choices=choices)

        return widgets

    @property
    def _field_is_required(self):
        """
        Property to determine if the field is a required field in the DB

        :return: Bool
        """
        return not self.model_field.blank and not self.model_field.null

    def get_context_data(self, **kwargs):
        """
        Custom implementation of get_context_data
        Adds data to the context required by the admin view

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Dict of context data for rendering the template
        """
        context_data = super(OmniModelFormCreateFieldView, self).get_context_data(**kwargs)
        context_data['model_field_name'] = self.model_field.name
        return context_data

    def get_initial(self):
        """
        Gets initial data for the form

        :return: Dict of initial data
        """
        initial = super(OmniModelFormCreateFieldView, self).get_initial()
        initial['required'] = self._field_is_required
        initial['label'] = self.model_field.verbose_name.capitalize()
        initial['name'] = self.model_field.name
        initial['widget_class'] = self.model.FORM_WIDGETS[0]
        if issubclass(self.model, OmniRelatedField):
            initial['related_type'] = ContentType.objects.get_for_model(self.model_field.rel.to).pk
        return initial


class OmniModelFormCreateHandlerView(OmniModelFormCreateRelatedView):
    """
    Creates a form handler for the specified form
    """
    template_name = 'admin/omniforms/omnimodelform/createhandler_form.html'
    permission_required = "omniforms.add_omniformhandler"
    add_another_url_name = 'admin:omniforms_omnimodelform_addhandler'

    def __init__(self, **kwargs):
        super(OmniModelFormCreateHandlerView, self).__init__(**kwargs)
        self.content_type_id = None

    def dispatch(self, request, *args, **kwargs):
        """
        Custom dispatch method
        Gets the omni form instance and sets the model for the view

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param request: Http Request instance
        :type request: django.http.HttpRequest
        """
        self.content_type_id = args[1]
        try:
            content_type = ContentType.objects.get(pk=self.content_type_id)
        except ContentType.DoesNotExist:
            raise Http404
        else:
            model_class = content_type.model_class()
            if not issubclass(model_class, OmniFormHandler) or model_class == OmniFormHandler:
                raise Http404
            self.model = model_class
        return super(OmniModelFormCreateHandlerView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Adds the handler content type id to the context

        :param kwargs: Default positional args
        :type kwargs: {}

        :return: Dict of context data for rendering the template
        """
        context_data = super(OmniModelFormCreateHandlerView, self).get_context_data(**kwargs)
        context_data['handler_content_type_id'] = self.content_type_id
        return context_data


class OmniModelFormPreviewView(OmniFormAdminView, DetailView):
    """
    Preview view for the omni model form
    """
    model = OmniModelForm
    template_name = 'admin/omniforms/omnimodelform/preview.html'
    permission_required = "omniforms.add_omnifield"

    def get_object(self, queryset=None):
        """
        Custom implementation of get_object

        :return: OmniModelForm instance
        """
        return self.omni_form

    def get_form_class(self):
        """
        Method for getting a form class for the preview view

        :return: Form class
        """
        return self.omni_form.get_form_class()

    def get_context_data(self, **kwargs):
        """
        Adds the omni form form instance to the context for the preview

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Dict of context data for the template
        """
        context_data = super(OmniModelFormPreviewView, self).get_context_data(**kwargs)
        context_data['form'] = self.get_form(self.get_form_class())
        return context_data
