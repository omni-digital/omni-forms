import django
from django import forms
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import Q
from django.template.loader import render_to_string

from omniforms.models import OmniForm, OmniField, OmniFormHandler


class WagtailOmniFormCloneForm(forms.ModelForm):
    """
    Form class for cloning an OmniForm
    """
    class Meta(object):
        """
        Django form meta
        """
        fields = ('title',)
        model = OmniForm

    def __init__(self, *args, **kwargs):
        """
        Ensures that the forms title field is not pre-filled

        :param args: Default positional args
        :param kwargs: Default keyword args
        """
        super(WagtailOmniFormCloneForm, self).__init__(*args, **kwargs)
        self.initial['title'] = None

    def save(self, commit=True):
        """
        Create a new form instance using the submitted title
        before cloning all fields associated with the source form
        and attaching them to the newly created OmniForm instance

        :param commit: Whether or not to commit the changes to the DB
        :return: Cloned form instance
        """
        instance = OmniForm.objects.create(title=self.cleaned_data['title'])

        # Clone the fields attached to the form
        for base_field in self.instance.fields.all():
            field = base_field.specific
            field.id = None
            field.omnifield_ptr = None
            field.form = instance
            field.save()

        # Clone the handlers attached to the form
        for base_handler in self.instance.handlers.all():
            handler = base_handler.specific
            handler.id = None
            handler.omniformhandler_ptr = None
            handler.form = instance
            handler.save()

        return instance


class OmniPermissionFormBase(forms.ModelForm):
    """
    Custom form class for rendering omniform permissions in the wagtail admin
    """
    class Meta(object):
        """
        Django properties
        """
        model = Group
        fields = ('permissions',)
        widgets = {'permissions': forms.CheckboxSelectMultiple()}

    @staticmethod
    def _checkboxes_by_id(bound_field):
        """
        Generates and returns a dict of checkbox fields keyed by permission ID

        :param bound_field: The bound form field to get permission checkboxes from
        :return: Dict of checkboxes keyed by permission ID
        """
        if django.VERSION < (1, 11):
            return {int(checkbox.choice_value): checkbox for checkbox in bound_field}
        return {int(checkbox.data['value']): checkbox for checkbox in bound_field}

    def as_admin_panel(self):
        """
        Required by the wagtail so that it can render the panel html when this
        form is registered using the register_group_permission_panel hook

        This code is basically taken from wagtails own 'format_permissions' template
        tag and modified/reduced to work with our specific use case

        :return: Rendered form panel
        """
        permissions = self.fields['permissions'].queryset
        checkboxes_by_id = self._checkboxes_by_id(self['permissions'])
        object_perms = []

        for content_type in ContentType.objects.filter(permission__in=permissions).distinct():
            content_perms_dict = {'object': content_type.name}
            for perm in permissions.filter(content_type=content_type):
                permission_action = perm.codename.split('_')[0]
                if permission_action in ['add', 'change', 'delete']:
                    content_perms_dict[permission_action] = checkboxes_by_id[perm.id]

            if content_perms_dict:
                object_perms.append(content_perms_dict)

        return render_to_string(
            'modeladmin/omniforms/wagtail/includes/permissions.html',
            {'title': self.admin_panel_title, 'object_perms': object_perms}
        )

    def save(self, commit=True):
        """
        We need to make sure we preserve permissions which are not managed by this form
        as such we get a queryset of all permissions associated with the forms model instance
        before calling super so that we may re-associate them with the instance after the form
        has been saved

        :param commit: Whether or not to commit the changes to the database
        :return: The saved group instance
        """
        # We need to read the permissions that:
        #  - have been applied to this group
        #  - are not managed by this form
        # We do this so that we can re-apply the original permissions once the permissions
        # that _are_ managed by this form are updated. Not doing this will mean we accidentally
        # blat out certain permissions on save.
        try:
            # Convert the permissions to a list as the queryset is evaluated lazily
            # and we need the permissions as they existed before the super classes
            # save method is called
            unmanaged_permissions = list(self.instance.permissions.exclude(pk__in=self.fields['permissions'].queryset))
        except ValueError:
            unmanaged_permissions = []
        group = super(OmniPermissionFormBase, self).save()
        group.permissions.add(*unmanaged_permissions)
        if commit:
            group.save()
        return group


class OmniFieldPermissionForm(OmniPermissionFormBase):
    """
    Custom form class for rendering omniform field permissions in the wagtail admin
    """
    admin_panel_title = 'OmniForm Fields'
    prefix = 'omnifield_permission'

    def __init__(self, *args, **kwargs):
        super(OmniFieldPermissionForm, self).__init__(*args, **kwargs)
        query = Q()
        for model_class in OmniField.objects.get_concrete_models():
            query |= Q(
                content_type__app_label=model_class._meta.app_label,
                content_type__model=model_class._meta.model_name
            )
        self.fields['permissions'].queryset = Permission.objects.filter(query).select_related('content_type')


class OmniHandlerPermissionForm(OmniPermissionFormBase):
    """
    Custom form class for rendering omniform field permissions in the wagtail admin
    """
    admin_panel_title = 'OmniForm Handlers'
    prefix = 'omnihandler_permission'

    def __init__(self, *args, **kwargs):
        super(OmniHandlerPermissionForm, self).__init__(*args, **kwargs)
        query = Q()
        for model_class in OmniFormHandler.objects.get_concrete_models():
            query |= Q(
                content_type__app_label=model_class._meta.app_label,
                content_type__model=model_class._meta.model_name
            )
        self.fields['permissions'].queryset = Permission.objects.filter(query).select_related('content_type')
