from django.conf.urls import url
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from wagtail.contrib.modeladmin.helpers.button import ButtonHelper
from wagtail.contrib.modeladmin.helpers.permission import PermissionHelper
from wagtail.contrib.modeladmin.helpers.url import AdminURLHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.wagtailcore import hooks

from omniforms.models import OmniForm
from omniforms.wagtail import model_admin_views
from omniforms.wagtail.forms import OmniFieldPermissionForm, OmniHandlerPermissionForm
from omniforms.wagtail.utils import run_permission_hooks


@hooks.register('register_permissions')
def add_omniforms_permissions():
    """
    Registers omniforms.OmniForm permissions with the wagtail admin

    :return: QuerySet of permissions for the omniforms.OmniForm model
    """
    return Permission.objects.filter(
        content_type__app_label="omniforms",
        content_type__model="omniform"
    )


@hooks.register('register_group_permission_panel')
def add_omnifields_permissions():
    """
    Registers a group permission panel in the wagtail admin
    for the management of OmniField model permissions

    :return: Form class for managing OmniField permissions
    """
    return OmniFieldPermissionForm


@hooks.register('register_group_permission_panel')
def add_omnihandlers_permissions():
    """
    Registers a group permission panel in the wagtail admin
    for the management of OmniFormHandler model permissions

    :return: Form class for managing OmniFormHandler permissions
    """
    return OmniHandlerPermissionForm


class WagtailOmniFormURLHelper(AdminURLHelper):
    """
    Custom url helper class
    Allows us to generate deeply nested urls for
    managing fields on an OmniForm model instance
    """
    def _get_object_specific_action_url_pattern(self, action):
        """
        Allows us to hook extra urls into the model admin

        :param action: View action to get the url pattern for
        :return:
        """
        if action == 'clone_form':
            return r'^{0}/{1}/{2}/(?P<instance_pk>[-\w]+)/$'.format(
                self.opts.app_label,
                self.opts.model_name,
                action
            )
        elif action == 'add_field':
            return r'^{0}/{1}/{2}/(?P<instance_pk>[-\w]+)/(?P<related_object_ctype_id>[\d]+)/$'.format(
                self.opts.app_label,
                self.opts.model_name,
                action
            )
        elif action in ('change_field', 'delete_field'):
            return r'^{0}/{1}/{2}/(?P<instance_pk>[-\w]+)/(?P<related_object_id>[\d]+)/$'.format(
                self.opts.app_label,
                self.opts.model_name,
                action
            )
        elif action == 'add_handler':
            return r'^{0}/{1}/{2}/(?P<instance_pk>[-\w]+)/(?P<related_object_ctype_id>[\d]+)/$'.format(
                self.opts.app_label,
                self.opts.model_name,
                action
            )
        elif action in ('change_handler', 'delete_handler'):
            return r'^{0}/{1}/{2}/(?P<instance_pk>[-\w]+)/(?P<related_object_id>[\d]+)/$'.format(
                self.opts.app_label,
                self.opts.model_name,
                action
            )
        return super(WagtailOmniFormURLHelper, self)._get_object_specific_action_url_pattern(action)


class WagtailOmniFormButtonHelper(ButtonHelper):
    """
    Custom button helper class
    Allows us to add a button to items on the list
    display for adding a field to the omni form
    """
    def add_field_button(self, pk, classnames_add=None, classnames_exclude=None):
        """
        Helper method for generating a button to display in the list view
        for the WagtailOmniForm ModelAdmin class. The button itself will
        be displayed in each row, next to the  edit and delete buttons

        :param pk: The primary key of the OmniForm model instance
        :param classnames_add: List of extra class names to add to the button
        :param classnames_exclude: List class names to remove from the button
        :return: Dict of data required to construct a button in the template
        """
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        classnames = self.edit_button_classnames + classnames_add
        classname = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('select_field', pk),
            'label': 'Add field',
            'classname': classname,
            'title': 'Add a new field',
        }

    def add_handler_button(self, pk, classnames_add=None, classnames_exclude=None):
        """
        Helper method for generating a button to display in the list view
        for the WagtailOmniForm ModelAdmin class. The button itself will
        be displayed in each row, next to the edit and delete buttons

        :param pk: The primary key of the OmniForm model instance
        :param classnames_add: List of extra class names to add to the button
        :param classnames_exclude: List class names to remove from the button
        :return: Dict of data required to construct a button in the template
        """
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        classnames = self.edit_button_classnames + classnames_add
        classname = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('select_handler', pk),
            'label': 'Add handler',
            'classname': classname,
            'title': 'Add a new handler',
        }

    def clone_form_button(self, pk, classnames_add=None, classnames_exclude=None):
        """
        Helper method for generating a button to display in the list view
        for the WagtailOmniForm ModelAdmin class. The button itself will
        be displayed in each row, next to the  edit and delete buttons

        :param pk: The primary key of the OmniForm model instance
        :param classnames_add: List of extra class names to add to the button
        :param classnames_exclude: List class names to remove from the button
        :return: Dict of data required to construct a button in the template
        """
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        classnames = self.edit_button_classnames + classnames_add
        classname = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('clone_form', pk),
            'label': 'Clone form',
            'classname': classname,
            'title': 'Clone form',
        }

    def get_buttons_for_obj(self, obj,
                            exclude=None,
                            classnames_add=None,
                            classnames_exclude=None):
        """
        Adds a button to the admin list view allowing a user to add
        a field to the OmniForm model instance (obj)

        :param obj: OmniForm model instance
        :param exclude: List of button names to exclude
        :param classnames_add: List of extra class names to add to the button
        :param classnames_exclude: List class names to remove from the button
        :return: List of button data dictionaries
        """
        buttons = super(WagtailOmniFormButtonHelper, self).get_buttons_for_obj(
            obj,
            exclude=exclude,
            classnames_add=classnames_add,
            classnames_exclude=classnames_exclude
        )

        # If the user can edit the form we assume they can also add fields
        if self.permission_helper.user_can_edit_obj(self.request.user, obj):
            buttons.append(
                self.add_field_button(obj.pk, classnames_add, classnames_exclude)
            )
            buttons.append(
                self.add_handler_button(obj.pk, classnames_add, classnames_exclude)
            )

        # If the user can edit the form we assume they can also add fields
        if self.permission_helper.user_can_clone_obj(self.request.user, obj):
            buttons.append(
                self.clone_form_button(obj.pk, classnames_add, classnames_exclude)
            )

        return buttons


class WagtailOmniFormPermissionHelper(PermissionHelper):
    """
    Custom permission helper class for Wagtail Omni forms
    """
    def user_can_clone_obj(self, user, obj):
        """
        Checks that the user has permission to clone a form in the system

        :param user: Logged in user instance
        :param obj: OmniForm model instance
        :return: bool - True if the user can create a form instance, otherwise false
        """
        try:
            run_permission_hooks('clone', obj)
        except PermissionDenied:
            return False
        else:
            perm_codename = self.get_perm_codename('add')
            return self.user_has_specific_permission(user, perm_codename)

    def user_can_edit_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'change'
        a specific `self.model` instance.
        """
        try:
            run_permission_hooks('update', obj)
        except PermissionDenied:
            return False
        else:
            return super(WagtailOmniFormPermissionHelper, self).user_can_edit_obj(user, obj)

    def user_can_delete_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'delete'
        a specific `self.model` instance.
        """
        try:
            run_permission_hooks('delete', obj)
        except PermissionDenied:
            return False
        else:
            return super(WagtailOmniFormPermissionHelper, self).user_can_delete_obj(user, obj)


class WagtailOmniFormModelAdmin(ModelAdmin):
    """
    Wagtail ModelAdmin class for the OmniForm model
    """
    model = OmniForm
    menu_label = 'Omni forms'
    menu_icon = 'form'
    menu_order = 1200
    add_to_settings_menu = False
    exclude_from_explorer = True
    list_display = ('title', 'omni_form_fields', 'omni_form_handlers', 'omni_form_locked', )
    search_fields = ('title', )
    form_fields_exclude = ('fields', 'handlers', )
    button_helper_class = WagtailOmniFormButtonHelper
    url_helper_class = WagtailOmniFormURLHelper
    permission_helper_class = WagtailOmniFormPermissionHelper
    # Custom model admin views
    clone_form_view_class = model_admin_views.CloneFormView
    select_field_view_class = model_admin_views.SelectFieldView
    add_field_view_class = model_admin_views.AddFieldView
    change_field_view_class = model_admin_views.ChangeFieldView
    delete_field_view_class = model_admin_views.DeleteFieldView
    select_handler_view_class = model_admin_views.SelectHandlerView
    add_handler_view_class = model_admin_views.AddHandlerView
    change_handler_view_class = model_admin_views.ChangeHandlerView
    delete_handler_view_class = model_admin_views.DeleteHandlerView

    def _omni_form_related(self, form, related_qs, change_action, delete_action):
        """
        Returns a comma delimited list of links for editing and deleting the related form objects

        :param form: OmniForm model instance
        :param related_qs: Queryset of related fields or handlers
        :param change_action: The name of the url change action
        :param delete_action: The name of the url delete action
        :return: comma delimited list of field links
        """
        links = []

        try:
            run_permission_hooks('update', form)
        except PermissionDenied:
            form_locked = True
        else:
            form_locked = False

        for related in related_qs:
            edit_url = self.url_helper.get_action_url(
                change_action,
                str(form.pk),
                str(related.pk)
            )

            delete_url = self.url_helper.get_action_url(
                delete_action,
                str(form.pk),
                str(related.pk)
            )

            links.append(render_to_string(
                'modeladmin/omniforms/wagtail/includes/related_controls.html',
                {
                    'button_text': related,
                    'edit_url': edit_url,
                    'delete_url': delete_url,
                    'form_locked': form_locked
                }
            ))
        return mark_safe(''.join(links))

    def omni_form_fields(self, instance):
        """
        Returns a comma delimited list of edit field links for the fields associated with the form

        :param instance: OmniForm model instance
        :return: comma delimited list of field links
        """
        return self._omni_form_related(
            instance,
            instance.fields.all(),
            'change_field',
            'delete_field'
        )

    def omni_form_handlers(self, instance):
        """
        Returns a comma delimited list of edit handler links for the fields associated with the form

        :param instance: OmniForm model instance
        :return: comma delimited list of field links
        """
        return self._omni_form_related(
            instance,
            instance.handlers.all(),
            'change_handler',
            'delete_handler'
        )

    @staticmethod
    def omni_form_locked(instance):
        """
        Determines if the omni form is locked and returns a string identifying this

        :param instance: The form instance
        :return: string
        """
        try:
            run_permission_hooks('update', instance)
            run_permission_hooks('delete', instance)
        except PermissionDenied:
            return 'yes'
        else:
            return 'no'

    def clone_form_view(self, request, instance_pk):
        """
        Instantiates a class-based view that allows the administrator to
        clone an existing omni form instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're cloning
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk}
        view_class = self.clone_form_view_class
        return view_class.as_view(**kwargs)(request)

    def select_field_view(self, request, instance_pk):
        """
        Instantiates a class-based view that allows the administrator to
        select the type of field to add to the omni form instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're adding a field to
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk}
        view_class = self.select_field_view_class
        return view_class.as_view(**kwargs)(request)

    def add_field_view(self, request, instance_pk, related_object_ctype_id):
        """
        Instantiates a class-based view that allows the administrator
        to add a field to the omni form model instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're adding a field to
        :param related_object_ctype_id: ID of the content type for the field type that we're adding to the form
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk, 'related_object_ctype_id': related_object_ctype_id}
        view_class = self.add_field_view_class
        return view_class.as_view(**kwargs)(request)

    def change_field_view(self, request, instance_pk, related_object_id):
        """
        Instantiates a class-based view that allows the administrator
        to change a field associated with the omni form model instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're changing a field on
        :param related_object_id: ID of the field we're changing
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk, 'related_object_id': related_object_id}
        view_class = self.change_field_view_class
        return view_class.as_view(**kwargs)(request)

    def delete_field_view(self, request, instance_pk, related_object_id):
        """
        Instantiates a class-based view that allows the administrator
        to delete a field associated with the omni form model instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're deleting a field from
        :param related_object_id: ID of the field we're deleting
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk, 'related_object_id': related_object_id}
        view_class = self.delete_field_view_class
        return view_class.as_view(**kwargs)(request)

    def select_handler_view(self, request, instance_pk):
        """
        Instantiates a class-based view that allows the administrator to
        select the type of handler to add to the omni form instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're adding a handler to
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk}
        view_class = self.select_handler_view_class
        return view_class.as_view(**kwargs)(request)

    def add_handler_view(self, request, instance_pk, related_object_ctype_id):
        """
        Instantiates a class-based view that allows the administrator
        to add a handler to the omni form model instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're adding a handler to
        :param related_object_ctype_id: ID of the content type for the handler that we're adding to the form
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk, 'related_object_ctype_id': related_object_ctype_id}
        view_class = self.add_handler_view_class
        return view_class.as_view(**kwargs)(request)

    def change_handler_view(self, request, instance_pk, related_object_id):
        """
        Instantiates a class-based view that allows the administrator
        to change a handler associated with the omni form model instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're changing a handler on
        :param related_object_id: ID of the handler we're changing
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk, 'related_object_id': related_object_id}
        view_class = self.change_handler_view_class
        return view_class.as_view(**kwargs)(request)

    def delete_handler_view(self, request, instance_pk, related_object_id):
        """
        Instantiates a class-based view that allows the administrator
        to delete a handler associated with the omni form model instance

        :param request: HttpRequest instance
        :param instance_pk: ID of the omni form we're deleting a handler from
        :param related_object_id: ID of the handler we're deleting
        :return: HttpResponse instance
        """
        kwargs = {'model_admin': self, 'instance_pk': instance_pk, 'related_object_id': related_object_id}
        view_class = self.delete_handler_view_class
        return view_class.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        """
        Adds extra urls for managing fields associated with the form

        :return: tuple of admin urls for the modeladmin class
        """
        return (
            url(
                self.url_helper.get_action_url_pattern('clone_form'),
                self.clone_form_view,
                name=self.url_helper.get_action_url_name('clone_form')
            ),
            url(
                self.url_helper.get_action_url_pattern('select_field'),
                self.select_field_view,
                name=self.url_helper.get_action_url_name('select_field')
            ),
            url(
                self.url_helper.get_action_url_pattern('add_field'),
                self.add_field_view,
                name=self.url_helper.get_action_url_name('add_field')
            ),
            url(
                self.url_helper.get_action_url_pattern('change_field'),
                self.change_field_view,
                name=self.url_helper.get_action_url_name('change_field')
            ),
            url(
                self.url_helper.get_action_url_pattern('delete_field'),
                self.delete_field_view,
                name=self.url_helper.get_action_url_name('delete_field')
            ),
            url(
                self.url_helper.get_action_url_pattern('select_handler'),
                self.select_handler_view,
                name=self.url_helper.get_action_url_name('select_handler')
            ),
            url(
                self.url_helper.get_action_url_pattern('add_handler'),
                self.add_handler_view,
                name=self.url_helper.get_action_url_name('add_handler')
            ),
            url(
                self.url_helper.get_action_url_pattern('change_handler'),
                self.change_handler_view,
                name=self.url_helper.get_action_url_name('change_handler')
            ),
            url(
                self.url_helper.get_action_url_pattern('delete_handler'),
                self.delete_handler_view,
                name=self.url_helper.get_action_url_name('delete_handler')
            ),
        ) + super(WagtailOmniFormModelAdmin, self).get_admin_urls_for_registration()


modeladmin_register(WagtailOmniFormModelAdmin)
