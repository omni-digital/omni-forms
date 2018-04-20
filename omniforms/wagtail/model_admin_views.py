from django import forms
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, redirect
from omniforms.admin_forms import AddRelatedForm, FieldForm
from omniforms.models import OmniField, OmniFormHandler
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView
from wagtail.wagtailadmin import messages

from omniforms.wagtail.forms import WagtailOmniFormCloneForm
from omniforms.wagtail.utils import run_permission_hooks


class OmniFormBaseView(ModelFormView, InstanceSpecificView):
    """
    Base view class for working with omni forms
    """
    @staticmethod
    def _get_model_permission(model_class, permission_type):
        """
        Given a model class and a permission type (e.g. add, change, delete) return
        a django permission string consisting of the app label and permission codename

        :param model_class:
        :param permission_type:
        :return:
        """
        return '{0}.{1}_{2}'.format(
            model_class._meta.app_label,
            permission_type,
            model_class._meta.model_name
        )

    def check_action_permitted(self, user):
        """
        Ensures that the user has permission to edit the omni form

        :param user: Logged in user instance
        :return: boolean - whether of not the user has permission to edit the instance
        """
        try:
            run_permission_hooks('update', self.instance)
        except PermissionDenied:
            return False
        else:
            return self.permission_helper.user_can_edit_obj(user, self.instance)

    def get_context_data(self, **kwargs):
        """
        Generates and returns a dictionary of context data to pass to the view

        :param kwargs: Default keyword arguments
        :return: Dictionary of template context data
        """
        context = {
            'view': self,
            'instance': self.get_instance(),
            'form': self.get_form(),
            'model_admin': self.model_admin,
        }
        context.update(kwargs)
        return context


class CloneFormView(OmniFormBaseView):
    """
    View class for cloning a form
    """
    template_name = 'modeladmin/omniforms/wagtail/clone_form.html'

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Clone form'

    def check_action_permitted(self, user):
        """
        Ensures that the user has permission to clone the omni form

        :param user: Logged in user instance
        :return: boolean - whether of not the user has permission to edit the instance
        """
        try:
            run_permission_hooks('clone', self.instance)
        except PermissionDenied:
            return False
        else:
            return self.permission_helper.user_can_clone_obj(user, self.instance)

    def get_form_class(self):
        """
        Returns the form class for the form displayed on this page

        :return: Form class for the view
        """
        return WagtailOmniFormCloneForm


class SelectRelatedView(OmniFormBaseView):
    """
    View for selecting related objects to add to an omni form
    """
    template_name = 'modeladmin/omniforms/wagtail/select_related.html'
    related_model_type = None
    excluded_models_setting_name = None
    success_redirect_url_name = None

    def get_form_class(self):
        """
        Returns the form class for the form displayed on this page

        :return: Form class for the view
        """
        return AddRelatedForm

    def get_form_kwargs(self):
        """
        Generates a dictionary of form kwargs to pass to the form constructor

        :return: Dict of form kwargs
        """
        form_kwargs = super(SelectRelatedView, self).get_form_kwargs()
        # ModelFormView expects a model form. However, we're using a
        # standard form class. As such we need to pop the OmniForm
        # instance out of the form keyword args
        form_kwargs.pop('instance', None)

        # We now need to add the form field choices ('choices') to
        # the form kwargs so that we can dynamically populate the
        # forms select box
        choices = []

        for instance in ContentType.objects.order_by('model'):
            model_class = instance.model_class()
            if not model_class:
                continue

            # Don't add the field to the form choices if the field is explicitly omitted
            if model_class.__name__ in getattr(settings, self.excluded_models_setting_name, []):
                continue

            if not issubclass(model_class, self.related_model_type):
                continue

            if model_class == self.related_model_type:
                continue

            perm = self._get_model_permission(model_class, 'add')
            if self.request.user.has_perm(perm):
                choices.append([instance.pk, instance.name])

        form_kwargs['choices'] = choices

        return form_kwargs

    def form_valid(self, form):
        """
        Redirects the user to the appropriate url on successful form submission

        :param form: Valid form instance
        :return: HttpResponseRedirect instance
        """
        instance = self.get_instance()
        redirect_url = self.url_helper.get_action_url(
            self.success_redirect_url_name,
            quote(instance.pk),
            form.cleaned_data['choices']
        )
        return redirect(redirect_url)


class SelectFieldView(SelectRelatedView):
    """
    View class for selecting a field to add to the omni form
    """
    related_model_type = OmniField
    excluded_models_setting_name = 'WAGTAIL_OMNI_FORM_OMITTED_FIELDS'
    success_redirect_url_name = 'add_field'

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Select field to add to form'


class SelectHandlerView(SelectRelatedView):
    """
    View class for selecting a handler to add to the omni form
    """
    related_model_type = OmniFormHandler
    excluded_models_setting_name = 'WAGTAIL_OMNI_FORM_OMITTED_HANDLERS'
    success_redirect_url_name = 'add_handler'

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Select handler to add to form'


class RelatedFormView(OmniFormBaseView):
    """
    View class for working with related form objects
    """
    base_form_class = forms.ModelForm
    related_object_model_class = None
    add_another_url_name = None
    template_name = 'modeladmin/omniforms/wagtail/related_form.html'

    def get_initial(self):
        """
        Adds the content_type and object_id for the omniform
        instance to the forms initial data

        :return: Dict of initial form data
        """
        omni_form = self.get_instance()
        initial = super(RelatedFormView, self).get_initial()
        initial.update({
            'content_type': ContentType.objects.get_for_model(omni_form).pk,
            'object_id': omni_form.pk
        })
        return initial

    def _get_form_widgets(self):
        """
        Returns a dict of form widgets keyed by field name

        :return: Dict of field widgets
        """
        widgets = {
            'object_id': forms.HiddenInput,
            'content_type': forms.HiddenInput,
        }

        return widgets

    def _get_help_texts(self):
        """
        Returns a dict of form help texts keyed by field name

        :return: Dict of field help texts
        """
        return {
            field.name: field.help_text
            for field in self.related_object_model_class._meta.fields
        }

    def _get_base_form_class(self):
        """
        Returns the base form class to use when constructing the model form for the
        related model type. Uses the form specified on the model class under the
        wagtail_base_model_class attribute (if it exists). Otherwise, falls back to
        use the base form class specified on the view

        :return: base form class
        """
        form_class = getattr(self.related_object_model_class, 'base_form_class', self.base_form_class)
        if not issubclass(form_class, forms.ModelForm):
            raise ImproperlyConfigured(
                '{0}._get_base_form_class must return a ModelForm or '
                'ModelForm subclass'.format(self.__class__.__name__)
            )
        return form_class

    def get_form_class(self):
        """
        Method for generating a form class for the view

        :return: ModelForm class
        """
        return forms.modelform_factory(
            self.related_object_model_class,
            exclude=['real_type'],
            form=self._get_base_form_class(),
            widgets=self._get_form_widgets(),
            help_texts=self._get_help_texts(),
        )

    def get_success_message_buttons(self, instance):
        """
        Overridden method to prevent buttons from being added to the success message

        :param instance: OmniForm model instance
        :return: empty list
        """
        return []

    def get_success_url(self):
        """
        If the 'save and add another' button was clicked,
        redirect to the select field view for the form

        :return: URL to redirect the user to
        """
        if 'save_and_add_another' in self.request.POST:
            return self.url_helper.get_action_url(self.add_another_url_name, self.instance.pk)
        return super(RelatedFormView, self).get_success_url()


class FieldFormView(RelatedFormView):
    """
    Base view class for working with omni fields
    """
    base_form_class = FieldForm
    add_another_url_name = 'select_field'

    def _get_form_widgets(self):
        """
        Returns a dict of form widgets keyed by field name

        :return: Dict of field widgets
        """
        widgets = super(FieldFormView, self)._get_form_widgets()
        widgets['widget_class'] = forms.HiddenInput(attrs={
            'value': self.related_object_model_class.FORM_WIDGETS[0]
        })

        if len(self.related_object_model_class.FORM_WIDGETS) > 1:
            choices = map(lambda x: (x, x.rsplit('.')[-1]), self.related_object_model_class.FORM_WIDGETS)
            widgets['widget_class'] = forms.Select(choices=choices)

        return widgets


class HandlerFormView(RelatedFormView):
    """
    Base view class for working with omni form handlers
    """
    base_form_class = forms.ModelForm
    add_another_url_name = 'select_handler'


class AddRelatedMixin(object):
    """
    Mixin class that holds abstracted logic for adding related fields/handlers to a form
    """
    related_object_ctype = None
    related_object_ctype_id = None
    related_object_model_class = None
    related_model_type = None
    excluded_models_setting_name = None

    def __init__(self, model_admin, instance_pk, related_object_ctype_id):
        """
        Allows a form field content type to be passed to the view constructor

        :param model_admin: Wagtail model admin instance
        :param instance_pk: Primary Key of the OmniForm instance we're editing
        :param related_object_ctype_id: The ContentType id for the field type we're adding to the form
        """
        super(AddRelatedMixin, self).__init__(model_admin, instance_pk)
        self.related_object_ctype_id = related_object_ctype_id

    def check_action_permitted(self, user):
        """
        Ensures that the user has permission to create the related object

        :param user: Logged in user instance
        :return: boolean - whether of not the user has permission to edit the instance
        """
        try:
            run_permission_hooks('create', self.instance)
        except PermissionDenied:
            return False
        else:
            return all([
                user.has_perm(self._get_model_permission(self.related_object_model_class, 'add')),
                self.permission_helper.user_can_edit_obj(user, self.instance)
            ])

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Add {0} to form'.format(self.related_object_ctype.name)

    def dispatch(self, request, *args, **kwargs):
        """
        Ensures that the form field content type both exists and is of the correct type

        :param request: HttpRequest instance
        :param args: default positional args
        :param kwargs: default keyword args
        :return: HttpResponse instance
        """
        self.related_object_ctype = get_object_or_404(ContentType, pk=self.related_object_ctype_id)
        self.related_object_model_class = self.related_object_ctype.model_class()

        # If the field that is being added is explicitly omitted from the choices return a 400
        if self.related_object_model_class.__name__ in getattr(settings, self.excluded_models_setting_name, []):
            return HttpResponseBadRequest()

        # If the field that is being added is a base field instance or is not an OmniField return a 400
        if self.related_object_model_class == self.related_model_type \
                or not issubclass(self.related_object_model_class, self.related_model_type):
            return HttpResponseBadRequest()

        return super(AddRelatedMixin, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Generates a dictionary of form kwargs to pass to the form constructor

        :return: Dict of form kwargs
        """
        form_kwargs = super(AddRelatedMixin, self).get_form_kwargs()
        form_kwargs['instance'] = self.related_object_model_class(form=self.instance)
        return form_kwargs


class AddFieldView(AddRelatedMixin, FieldFormView):
    """
    View class for adding a field to the omni form instance
    """
    related_model_type = OmniField
    excluded_models_setting_name = 'WAGTAIL_OMNI_FORM_OMITTED_FIELDS'

    def get_success_message(self, instance):
        """
        Returns text for the message to display in the UI when a
        successful form submission has been processed

        :param instance: The created model instance
        :return: success message text
        """
        return "Form field successfully created"


class AddHandlerView(AddRelatedMixin, HandlerFormView):
    """
    View class for adding a handler to the omni form instance
    """
    related_model_type = OmniFormHandler
    excluded_models_setting_name = 'WAGTAIL_OMNI_FORM_OMITTED_HANDLERS'

    def get_success_message(self, instance):
        """
        Returns text for the message to display in the UI when a
        successful form submission has been processed

        :param instance: The created model instance
        :return: success message text
        """
        return "Form handler successfully created"


class RelatedObjectInstanceMixin(object):
    """
    Mixin class for working with persisted form field instances
    """
    related_object = None
    related_object_id = None
    related_object_model_class = None
    related_object_base_model_class = None

    def __init__(self, model_admin, instance_pk, related_object_id):
        """
        Allows a form field id to be passed to the view constructor

        :param model_admin: Wagtail model admin instance
        :param instance_pk: Primary Key of the OmniForm instance we're editing
        :param related_object_id: ID of the related_object to be changed
        """
        super(RelatedObjectInstanceMixin, self).__init__(model_admin, instance_pk)
        self.related_object_id = related_object_id

    def dispatch(self, request, *args, **kwargs):
        """
        Ensures that the form field content type both exists and is of the correct type

        :param request: HttpRequest instance
        :param args: default positional args
        :param kwargs: default keyword args
        :return: HttpResponse instance
        """
        base_instance = get_object_or_404(self.related_object_base_model_class, pk=self.related_object_id)
        self.related_object = base_instance.specific
        self.related_object_model_class = self.related_object.__class__
        if self.related_object.object_id != self.instance.pk:
            raise Http404
        return super(RelatedObjectInstanceMixin, self).dispatch(request, *args, **kwargs)


class ChangeRelatedObjectInstanceMixin(RelatedObjectInstanceMixin):
    """
    Mixin class for changing a related instance
    """
    def check_action_permitted(self, user):
        """
        Ensures that the user has permission to change the related object

        :param user: Logged in user instance
        :return: boolean - whether of not the user has permission to edit the instance
        """
        try:
            run_permission_hooks('update', self.instance)
        except PermissionDenied:
            return False
        else:
            return all([
                user.has_perm(self._get_model_permission(self.related_object_model_class, 'change')),
                self.permission_helper.user_can_edit_obj(user, self.instance)
            ])

    def get_form_kwargs(self):
        """
        Generates a dictionary of form kwargs to pass to the form constructor

        :return: Dict of form kwargs
        """
        form_kwargs = super(ChangeRelatedObjectInstanceMixin, self).get_form_kwargs()
        form_kwargs['instance'] = self.related_object
        return form_kwargs


class ChangeFieldView(ChangeRelatedObjectInstanceMixin, FieldFormView):
    """
    View class for changing a field associated with the omni form instance
    """
    related_object_base_model_class = OmniField

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Change {0} field'.format(self.related_object.label)

    def get_success_message(self, instance):
        """
        Returns text for the message to display in the UI when a
        successful form submission has been processed

        :param instance: The created model instance
        :return: success message text
        """
        return "Form field successfully updated"


class ChangeHandlerView(ChangeRelatedObjectInstanceMixin, HandlerFormView):
    """
    View class for changing a Handler associated with the omni form instance
    """
    related_object_base_model_class = OmniFormHandler

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Change {0} handler'.format(self.related_object.name)

    def get_success_message(self, instance):
        """
        Returns text for the message to display in the UI when a
        successful form submission has been processed

        :param instance: The created model instance
        :return: success message text
        """
        return "Form handler successfully updated"


class DeleteRelatedObjectView(RelatedObjectInstanceMixin, OmniFormBaseView):
    """
    Mixin class for changing a related instance
    """
    template_name = 'modeladmin/omniforms/wagtail/delete_related.html'

    def check_action_permitted(self, user):
        """
        Ensures that the user has permission to change the related object

        :param user: Logged in user instance
        :return: boolean - whether of not the user has permission to edit the instance
        """
        try:
            run_permission_hooks('delete', self.instance)
        except PermissionDenied:
            return False
        else:
            return all([
                user.has_perm(self._get_model_permission(self.related_object_model_class, 'delete')),
                self.permission_helper.user_can_edit_obj(user, self.instance)
            ])

    def get_form_class(self):
        """
        Returns the form class for the form displayed on this page

        :return: Form class for the view
        """
        return forms.Form

    def get_form_kwargs(self):
        """
        Generates a dictionary of form kwargs to pass to the form constructor

        :return: Dict of form kwargs
        """
        form_kwargs = super(DeleteRelatedObjectView, self).get_form_kwargs()
        # ModelFormView expects a model form. However, we're using a
        # standard form class. As such we need to pop the OmniForm
        # instance out of the form keyword args
        form_kwargs.pop('instance', None)
        return form_kwargs

    def form_valid(self, form):
        """
        Deletes the form field and redirects to the index view

        :param form: Valid form instance
        :return: HttpResponseRedirect instance
        """
        messages.success(
            self.request, self.get_success_message(self.related_object),
            buttons=self.get_success_message_buttons(self.related_object)
        )
        self.related_object.delete()
        return redirect(self.index_url)

    def get_context_data(self, **kwargs):
        """
        Adds the form field to the template context data

        :param kwargs: Default keyword args
        :return: Dict of template context data
        """
        ctx = super(DeleteRelatedObjectView, self).get_context_data(**kwargs)
        ctx['object'] = self.related_object
        return ctx


class DeleteFieldView(DeleteRelatedObjectView):
    """
    Simple view for deleting a field from the specified omni form
    """
    related_object_base_model_class = OmniField

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Delete {0} field'.format(self.related_object.label)

    def get_success_message(self, instance):
        """
        Returns text for the message to display in the UI when a
        successful form submission has been processed

        :param instance: The created model instance
        :return: success message text
        """
        return "{0} has been deleted".format(instance.label)


class DeleteHandlerView(DeleteRelatedObjectView):
    """
    Simple view for deleting a field from the specified omni form
    """
    related_object_base_model_class = OmniFormHandler

    def get_page_title(self):
        """
        Returns the page title for this view

        :return: Page title
        """
        return 'Delete {0} handler'.format(self.related_object.name)

    def get_success_message(self, instance):
        """
        Returns text for the message to display in the UI when a
        successful form submission has been processed

        :param instance: The created model instance
        :return: success message text
        """
        return "{0} has been deleted".format(instance.name)
