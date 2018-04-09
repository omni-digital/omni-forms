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
from django.views.generic import FormView, CreateView, DetailView, UpdateView
from omniforms.admin_forms import AddRelatedForm, FieldForm
from omniforms.models import OmniForm, OmniModelForm, OmniField, OmniRelatedField, OmniFormHandler


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
    omni_form_model_class = None

    def __init__(self, **kwargs):
        """
        Sets up attributes required for the view

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniFormAdminView, self).__init__(**kwargs)
        self.omni_form = None

    def _load_omni_form(self, pk):
        """
        Loads the omin form instance from the database or raises an HTTP 404

        :param pk: The id of the omni form instance
        :type pk: int

        :return: OmniForm model instance
        """
        return get_object_or_404(self.omni_form_model_class, pk=pk)

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


class SelectRelatedView(OmniFormAdminView):
    """
    View for selecting a related model type to add to the Omni Form instance in the django admin
    This view does not actually create the related instance but allows the administrator to select the
    type of related object that should be attached to the omni form
    """
    template_name = None
    permission_required = None
    url_name = None
    omni_form_model_class = None
    form_class = None

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
        form_kwargs = super(SelectRelatedView, self).get_form_kwargs()
        form_kwargs['choices'] = self._get_form_choices()
        return form_kwargs

    def form_valid(self, form):
        """
        Called when the submitted form is valid

        :param form: Valid form instance
        :type form: omniforms.admin_forms.AddRelatedForm

        :return: Http Response
        """
        url = reverse(self.url_name, args=(self.omni_form.pk, form.cleaned_data['choices']))
        return HttpResponseRedirect(url)


class RelatedView(OmniFormAdminView):
    """
    View class for Creating/Updating OmniForm related objects
    """
    model = None
    add_another_url_name = None
    change_url_name = None
    form_class = forms.ModelForm
    exclude = ('real_type',)

    def get_initial(self):
        """
        Gets initial data for the form

        :return: Dict of initial data
        """
        initial = super(RelatedView, self).get_initial()
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

    def _get_help_texts(self):
        """
        Returns a dict of form help texts keyed by field name

        :return: Dict of field help texts
        """
        return {
            field.name: field.help_text
            for field in self.model._meta.fields
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
            widgets=self._get_form_widgets(),
            help_texts=self._get_help_texts(),
        )

    def get_success_url(self):
        """
        Method for getting the success URL to redirect the user to on successful form submission

        :return: Url to redirect the user to
        """
        if '_addanother' in self.request.POST:
            return reverse(self.add_another_url_name, args=[self.omni_form.pk])
        else:
            return reverse(self.change_url_name, args=[self.omni_form.pk])


class SelectHandlerViewMixin(object):
    """
    View for choosing a handler to add to the Omni Model Form instance in the django admin
    """
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


class CreateHandlerView(CreateView):
    """
    Creates a form handler for the specified form
    """
    omni_form = None
    template_name = None
    permission_required = "omniforms.add_omniformhandler"

    def __init__(self, **kwargs):
        super(CreateHandlerView, self).__init__(**kwargs)
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
        return super(CreateHandlerView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Creates a handler instance to add to the form so that help text can be generated correctly

        :return: Dict of keyword args to be used when instanciating the form
        """
        form_kwargs = super(CreateHandlerView, self).get_form_kwargs()
        form_kwargs['instance'] = self.model(form=self.omni_form)
        return form_kwargs

    def get_context_data(self, **kwargs):
        """
        Adds the handler content type id to the context

        :param kwargs: Default positional args
        :type kwargs: {}

        :return: Dict of context data for rendering the template
        """
        context_data = super(CreateHandlerView, self).get_context_data(**kwargs)
        context_data['handler_content_type_id'] = self.content_type_id
        return context_data


class UpdateHandlerView(UpdateView):
    """
    View class for updating an existing handler
    """
    permission_required = "omniforms.change_omniformhandler"
    template_name = None

    def __init__(self, **kwargs):
        super(UpdateHandlerView, self).__init__(**kwargs)
        self.object = None

    def get_object(self, queryset=None):
        """
        Gets the handler instance for editing

        :param queryset: Queryset from which to get the handler instance
        :type queryset: django.db.models.Queryset

        :return: Omni Model Form Handler instance
        """
        try:
            return self.omni_form.handlers.get(pk=self.args[1]).specific
        except OmniFormHandler.DoesNotExist:
            raise Http404

    def dispatch(self, request, *args, **kwargs):
        """
        Custom dispatch method
        Loads the omni form, gets the handler and sets the model class on the view accordingly

        :param request: Http Request instance
        :type request: django.http.HttpRequest

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Http Response
        """
        self.omni_form = self._load_omni_form(args[0])
        self.object = self.get_object()
        self.model = self.object.__class__
        return super(UpdateHandlerView, self).dispatch(request, *args, **kwargs)


class PreviewView(DetailView):
    """
    Preview view for the omni model form
    """
    omni_form = None

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
        context_data = super(PreviewView, self).get_context_data(**kwargs)
        context_data['form'] = self.get_form(self.get_form_class())
        return context_data


class OmniModelFormSelectRelatedView(SelectRelatedView):
    """
    View for selecting a related model type to add to the Omni Model Form instance in the django admin
    This view does not actually create the related instance but allows the administrator to select the
    type of related object that should be attached to the omni form
    """
    omni_form_model_class = OmniModelForm
    form_class = AddRelatedForm


class OmniModelFormRelatedView(RelatedView):
    """
    View class for Creating/Updating OmniForm related objects
    """
    omni_form_model_class = OmniModelForm
    change_url_name = 'admin:omniforms_omnimodelform_change'


class OmniModelFormSelectFieldView(OmniModelFormSelectRelatedView):
    """
    View for choosing which field a field to the Omni Model Form instance in the django admin
    """
    template_name = "admin/omniforms/base/selectfield_form.html"
    permission_required = "omniforms.add_omnifield"
    url_name = 'admin:omniforms_omnimodelform_createfield'

    def _get_form_choices(self):
        """
        Custom implementation of get_form_kwargs
        Adds a list of model fields to the kwargs for use in the form

        :return: Dict of kwargs for the form
        """
        return self.omni_form.get_model_field_choices()


class OmniModelFormSelectHandlerView(SelectHandlerViewMixin, OmniModelFormSelectRelatedView):
    """
    View for choosing a handler to add to the Omni Model Form instance in the django admin
    """
    template_name = "admin/omniforms/base/selecthandler_form.html"
    permission_required = "omniforms.add_omniformhandler"
    url_name = 'admin:omniforms_omnimodelform_createhandler'


class OmniModelFormFieldView(OmniModelFormRelatedView):
    """
    View for creating/editing OmniModelForm fields
    """
    add_another_url_name = 'admin:omniforms_omnimodelform_addfield'
    form_class = FieldForm
    model = None

    def __init__(self, *args, **kwargs):
        """
        Sets up attributes required for the view

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniModelFormFieldView, self).__init__(*args, **kwargs)
        self.model_field = None
        self.object = None

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
        self.omni_form = self._load_omni_form(args[0])
        try:
            self.model_field = self.omni_form.content_type.model_class()._meta.get_field(args[1])
        except FieldDoesNotExist:
            raise Http404
        self.model = OmniField.get_concrete_class_for_model_field(self.model_field)
        return super(OmniModelFormFieldView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Custom implementation of get_object
        Returns the field with the specified name belonging to the omni form

        :param queryset: Queryset of model instances to get the model instance from
        :type queryset: django.db.models.query.QuerySet

        :return: OmniField model instance
        """
        try:
            return self.omni_form.fields.get(name=self.args[1])
        except OmniField.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        """
        Custom implementation of get_context_data
        Adds data to the context required by the admin view

        :param kwargs: Default keyword args
        :type kwargs: {}

        :return: Dict of context data for rendering the template
        """
        context_data = super(OmniModelFormFieldView, self).get_context_data(**kwargs)
        context_data['model_field_name'] = self.model_field.name
        return context_data

    def _get_form_widgets(self):
        """
        Returns a dict of form widgets keyed by field name

        :return: Dict of field widgets
        """
        widgets = super(OmniModelFormFieldView, self)._get_form_widgets()
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


class OmniModelFormCreateFieldView(OmniModelFormFieldView, CreateView):
    """
    Creates a form field for the specified form
    """
    template_name = 'admin/omniforms/base/field_form.html'
    permission_required = "omniforms.add_omnifield"

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
        self.omni_form = self._load_omni_form(args[0])
        if args[1] not in self.omni_form.get_model_field_names():
            raise Http404
        if args[1] in self.omni_form.used_field_names:
            raise Http404
        return super(OmniModelFormCreateFieldView, self).dispatch(request, *args, **kwargs)

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


class OmniModelFormUpdateFieldView(OmniModelFormFieldView, UpdateView):
    """
    View class for updating an existing field
    """
    permission_required = "omniforms.change_omnifield"
    template_name = 'admin/omniforms/base/field_form.html'


class OmniModelFormHandlerView(OmniModelFormRelatedView):
    """
    View for creating/editing OmniModelForm handlers
    """
    add_another_url_name = 'admin:omniforms_omnimodelform_addhandler'


class OmniModelFormCreateHandlerView(CreateHandlerView, OmniModelFormHandlerView):
    """
    Creates a form handler for the specified form
    """
    template_name = 'admin/omniforms/base/handler_form.html'
    permission_required = "omniforms.add_omniformhandler"


class OmniModelFormUpdateHandlerView(UpdateHandlerView, OmniModelFormHandlerView):
    """
    View class for updating an existing handler
    """
    template_name = 'admin/omniforms/base/handler_form.html'


class OmniModelFormPreviewView(PreviewView, OmniFormAdminView):
    """
    Preview view for the omni model form
    """
    model = OmniModelForm
    omni_form_model_class = OmniModelForm
    template_name = 'admin/omniforms/base/preview.html'
    permission_required = "omniforms.add_omnifield"


class OmniFormSelectRelatedView(SelectRelatedView):
    """
    View for selecting a related model type to add to the Omni Form instance in the django admin
    This view does not actually create the related instance but allows the administrator to select the
    type of related object that should be attached to the omni form
    """
    omni_form_model_class = OmniForm
    form_class = AddRelatedForm


class OmniFormRelatedView(RelatedView):
    """
    View class for Creating/Updating OmniForm related objects
    """
    omni_form_model_class = OmniForm
    change_url_name = 'admin:omniforms_omniform_change'


class OmniFormFieldView(OmniFormRelatedView):
    """
    View for creating/editing OmniModelForm fields
    """
    add_another_url_name = 'admin:omniforms_omniform_addfield'
    form_class = FieldForm
    model = None

    def __init__(self, *args, **kwargs):
        """
        Sets up attributes required for the view

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniFormFieldView, self).__init__(*args, **kwargs)
        self.model_field = None
        self.object = None

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
        self.omni_form = self._load_omni_form(args[0])
        try:
            self.model = ContentType.objects.get(pk=args[1]).model_class()
        except ContentType.DoesNotExist:
            raise Http404
        return super(OmniFormFieldView, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Custom implementation of get_object
        Returns the field with the specified name belonging to the omni form

        :param queryset: Queryset of model instances to get the model instance from
        :type queryset: django.db.models.query.QuerySet

        :return: OmniField model instance
        """
        try:
            return self.omni_form.fields.get(name=self.args[2])
        except OmniField.DoesNotExist:
            raise Http404

    def _get_form_widgets(self):
        """
        Returns a dict of form widgets keyed by field name

        :return: Dict of field widgets
        """
        widgets = super(OmniFormFieldView, self)._get_form_widgets()
        widgets.update({
            'widget_class': forms.HiddenInput(attrs={
                'value': self.model.FORM_WIDGETS[0]
            }),
        })

        if len(self.model.FORM_WIDGETS) > 1:
            choices = map(lambda x: (x, x.rsplit('.')[-1]), self.model.FORM_WIDGETS)
            widgets['widget_class'] = forms.Select(choices=choices)

        return widgets

    def get_form_class(self):
        """
        Method for generating a form class for the view

        :return: ModelForm class
        """
        return modelform_factory(
            self.model,
            exclude=self.exclude,
            form=self.form_class,
            widgets=self._get_form_widgets(),
            help_texts=self._get_help_texts(),
        )


class OmniFormSelectFieldView(OmniFormSelectRelatedView):
    """
    View for choosing which field a field to the Omni Form instance in the django admin
    """
    template_name = "admin/omniforms/base/selectfield_form.html"
    permission_required = "omniforms.add_omnifield"
    url_name = 'admin:omniforms_omniform_createfield'

    def _get_form_choices(self):
        """
        Custom implementation of get_form_kwargs
        Adds a list of model fields to the kwargs for use in the form

        :return: Dict of kwargs for the form
        """
        return [
            [instance.pk, instance.name] for instance in ContentType.objects.order_by('model')
            if instance.model_class() is not None
            and issubclass(instance.model_class(), OmniField)
            and instance.model_class() != OmniField
        ]


class OmniFormCreateFieldView(OmniFormFieldView, CreateView):
    """
    Creates a form field for the specified form
    """
    template_name = 'admin/omniforms/base/field_form.html'
    permission_required = "omniforms.add_omnifield"

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
        self.omni_form = self._load_omni_form(args[0])
        return super(OmniFormCreateFieldView, self).dispatch(request, *args, **kwargs)


class OmniFormUpdateFieldView(OmniFormFieldView, UpdateView):
    """
    View class for updating an existing field
    """
    permission_required = "omniforms.change_omnifield"
    template_name = 'admin/omniforms/base/field_form.html'


class OmniFormSelectHandlerView(SelectHandlerViewMixin, OmniFormSelectRelatedView):
    """
    View for choosing a handler to add to the Omni Form instance in the django admin
    """
    template_name = "admin/omniforms/base/selecthandler_form.html"
    permission_required = "omniforms.add_omniformhandler"
    url_name = 'admin:omniforms_omniform_createhandler'


class OmniFormHandlerView(OmniFormRelatedView):
    """
    View for creating/editing OmniForm handlers
    """
    add_another_url_name = 'admin:omniforms_omniform_addhandler'


class OmniFormCreateHandlerView(CreateHandlerView, OmniFormHandlerView):
    """
    Creates a form handler for the specified form
    """
    template_name = 'admin/omniforms/base/handler_form.html'
    permission_required = "omniforms.add_omniformhandler"


class OmniFormUpdateHandlerView(UpdateHandlerView, OmniFormHandlerView):
    """
    View class for updating an existing handler
    """
    template_name = 'admin/omniforms/base/handler_form.html'


class OmniFormPreviewView(PreviewView, OmniFormAdminView):
    """
    Preview view for the omni form
    """
    model = OmniForm
    omni_form_model_class = OmniForm
    template_name = 'admin/omniforms/base/preview.html'
    permission_required = "omniforms.add_omnifield"
