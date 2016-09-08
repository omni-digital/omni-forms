# -*- coding: utf-8 -*-
"""
Models for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.files import File
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.fields.related import ForeignObjectRel
from django.forms import modelform_factory
from django.template import Template, Context
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from omniforms.forms import OmniModelFormBaseForm
import re


@python_2_unicode_compatible
class OmniField(models.Model):
    """
    Base class for omni fields
    """
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    help_text = models.TextField(blank=True, null=True)
    required = models.BooleanField(default=False)
    widget_class = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    real_type = models.ForeignKey(ContentType, related_name='+')  # The Real OmniField type (set in the save method)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    form = GenericForeignKey()

    class Meta(object):
        """
        Django properties
        """
        ordering = ('order',)
        unique_together = ('name', 'content_type', 'object_id')

    def __str__(self):
        """
        String representation of the instance

        :return: Fields label
        """
        return self.label

    @classmethod
    def get_custom_field_mapping(cls):
        """
        Class method for getting custom, user defined, field mappings

        :return: Field mapping dict where the key is a model field class and the value is an OmniField subclass
        """
        field_mapping = {}
        custom_fields = getattr(settings, 'OMNI_FORMS_CUSTOM_FIELD_MAPPING', {})
        for key, value in custom_fields.items():
            try:
                field_mapping_key = import_string(key)
            except ImportError:
                raise ImproperlyConfigured(
                    'Could not import \'{0}\' from settings.OMNI_FORMS_CUSTOM_FIELD_MAPPING '
                    'Please update your settings file'.format(key)
                )

            try:
                field_mapping_value = import_string(value)
            except ImportError:
                raise ImproperlyConfigured(
                    'Could not import \'{0}\' from \'settings.OMNI_FORMS_CUSTOM_FIELD_MAPPING[{1}].\''
                    'Please update your settings file'.format(value, key)
                )
            else:
                if not issubclass(field_mapping_value, OmniField):
                    raise ImproperlyConfigured('\'{0}\' defined in OMNI_FORMS_CUSTOM_FIELD_MAPPING must be a '
                                               'subclass of omniforms.models.OmniField'.format(value))

            field_mapping[field_mapping_key] = field_mapping_value
        return field_mapping

    @classmethod
    def get_concrete_class_for_model_field(cls, model_field):
        """
        Method for getting a concrete model class to represent the type of form field required

        :param model_field: Model Field instance
        :return: OmniField subclass
        """
        field_mapping = {
            models.CharField: OmniCharField,
            models.TextField: OmniCharField,
            models.BooleanField: OmniBooleanField,
            models.NullBooleanField: OmniBooleanField,
            models.DateField: OmniDateField,
            models.DateTimeField: OmniDateTimeField,
            models.DecimalField: OmniDecimalField,
            models.EmailField: OmniEmailField,
            models.FloatField: OmniFloatField,
            models.IntegerField: OmniIntegerField,
            models.BigIntegerField: OmniIntegerField,
            models.PositiveIntegerField: OmniIntegerField,
            models.PositiveSmallIntegerField: OmniIntegerField,
            models.SmallIntegerField: OmniIntegerField,
            models.CommaSeparatedIntegerField: OmniCharField,
            models.TimeField: OmniTimeField,
            models.URLField: OmniUrlField,
            models.ForeignKey: OmniForeignKeyField,
            models.ManyToManyField: OmniManyToManyField,
            models.SlugField: OmniSlugField,
            models.FileField: OmniFileField,
            models.ImageField: OmniImageField,
            models.DurationField: OmniDurationField,
            models.GenericIPAddressField: OmniGenericIPAddressField
        }
        field_mapping.update(cls.get_custom_field_mapping())
        return field_mapping.get(model_field.__class__)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Custom save method
        Sets the actual content type on the instance if it doesn't exist already

        :param force_insert: Whether or not to force the insert
        :type force_insert: bool

        :param force_update: Whether or not to force the update
        :type force_update: bool

        :param using: Database connection to use
        :type using: connection

        :param update_fields: Fields to update
        :type update_fields: list

        :return: Saved instance
        """
        if not self.real_type_id:
            self.real_type = ContentType.objects.get_for_model(self)
        super(OmniField, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    @cached_property
    def specific(self):
        """
        Method for getting the most specific subclassed version of this instance

        :return: OmniField model subclass instance
        """
        real_type = self.real_type
        if isinstance(self, real_type.model_class()):
            return self
        else:
            return self.real_type.get_object_for_this_type(pk=self.pk)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        field_class = import_string(self.specific.FIELD_CLASS)
        widget_class = import_string(self.specific.widget_class)
        return field_class(
            widget=widget_class(),
            label=self.specific.label,
            help_text=self.specific.help_text,
            required=self.specific.required,
            initial=self.specific.initial,
            **kwargs
        )

    def get_edit_url(self):
        """
        Generates a URL for editing the field in the django admin

        :return: Edit URL for the admin interface
        """
        return reverse('admin:omniforms_omnimodelform_updatefield', args=[self.object_id, self.name])


class OmniCharField(OmniField):
    """
    CharField representation
    """
    initial = models.TextField(blank=True, null=True)
    max_length = models.PositiveIntegerField(default=255, blank=True)
    min_length = models.PositiveIntegerField(default=0, blank=True)

    FIELD_CLASS = 'django.forms.CharField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.Textarea',
        'django.forms.widgets.PasswordInput'
    )

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniCharField, self).as_form_field(
            min_length=self.min_length,
            max_length=self.max_length
        )


class OmniDurationField(OmniField):
    """
    DurationField representation
    """
    initial = models.DurationField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.DurationField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.Textarea'
    )


class OmniGenericIPAddressField(OmniField):
    """
    GenericIPAddressField representation
    """
    PROTOCOL_BOTH = 'both'
    PROTOCOL_IPV4 = 'IPv4'
    PROTOCOL_IPV6 = 'IPv6'
    PROTOCOL_CHOICES = (
        (PROTOCOL_BOTH, 'Both'),
        (PROTOCOL_IPV4, 'IPv4'),
        (PROTOCOL_IPV6, 'IPv6')
    )

    initial = models.GenericIPAddressField(blank=True, null=True)
    protocol = models.CharField(max_length=4, blank=True, choices=PROTOCOL_CHOICES, default=PROTOCOL_BOTH)
    unpack_ipv4 = models.BooleanField(default=False, blank=True)

    FIELD_CLASS = 'django.forms.GenericIPAddressField'
    FORM_WIDGETS = ('django.forms.widgets.TextInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniGenericIPAddressField, self).as_form_field(
            protocol=self.protocol,
            unpack_ipv4=self.unpack_ipv4
        )

    def clean(self):
        """
        Cleans the model data
        Ensures that unpack_ipv4 is only enabled if protocol is set to 'both'

        :raises: ValidationError
        """
        if self.unpack_ipv4 and self.protocol != self.PROTOCOL_BOTH:
            raise ValidationError(
                'You may only select the \'unpack ipv4\' option if '
                'the protocol you have selected is \'Both\''
            )


class OmniUUIDField(OmniField):
    """
    UUIDField representation
    """
    initial = models.UUIDField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.UUIDField'
    FORM_WIDGETS = ('django.forms.widgets.TextInput',)


class OmniSlugField(OmniField):
    """
    SlugField representation
    """
    initial = models.SlugField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.SlugField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.HiddenInput'
    )


class OmniBooleanField(OmniField):
    """
    BooleanField representation
    """
    initial = models.NullBooleanField()
    FIELD_CLASS = 'django.forms.BooleanField'
    FORM_WIDGETS = ('django.forms.widgets.CheckboxInput',)


class OmniDateField(OmniField):
    """
    DateField representation
    """
    initial = models.DateField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.DateField'
    FORM_WIDGETS = ('django.forms.widgets.DateInput',)


class OmniDateTimeField(OmniField):
    """
    DateTimeField representation
    """
    initial = models.DateTimeField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.DateTimeField'
    FORM_WIDGETS = ('django.forms.widgets.DateTimeInput',)


class OmniDecimalField(OmniField):
    """
    DecimalField representation
    """
    initial = models.DecimalField(blank=True, null=True, decimal_places=100, max_digits=1000)
    min_value = models.DecimalField(blank=True, null=True, decimal_places=100, max_digits=1000)
    max_value = models.DecimalField(blank=True, null=True, decimal_places=100, max_digits=1000)
    max_digits = models.PositiveIntegerField()
    decimal_places = models.PositiveIntegerField()

    FIELD_CLASS = 'django.forms.DecimalField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniDecimalField, self).as_form_field(
            min_value=self.min_value,
            max_value=self.max_value,
            max_digits=self.max_digits,
            decimal_places=self.decimal_places
        )


class OmniEmailField(OmniField):
    """
    EmailField representation
    """
    initial = models.EmailField(blank=True, null=True)
    max_length = models.PositiveIntegerField(default=255, blank=True)
    min_length = models.PositiveIntegerField(default=0, blank=True)

    FIELD_CLASS = 'django.forms.EmailField'
    FORM_WIDGETS = ('django.forms.widgets.EmailInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniEmailField, self).as_form_field(
            min_length=self.min_length,
            max_length=self.max_length
        )


class OmniFileField(OmniField):
    """
    FileField representation
    """
    initial = None
    max_length = models.PositiveIntegerField(blank=True, null=True)
    allow_empty_file = models.BooleanField(default=False)

    FIELD_CLASS = 'django.forms.FileField'
    FORM_WIDGETS = ('django.forms.widgets.FileInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniFileField, self).as_form_field(
            max_length=self.max_length,
            allow_empty_file=self.allow_empty_file
        )


class OmniImageField(OmniField):
    """
    ImageField representation
    """
    initial = None
    FIELD_CLASS = 'django.forms.ImageField'
    FORM_WIDGETS = ('django.forms.widgets.FileInput',)


class OmniFloatField(OmniField):
    """
    FloatField representation
    """
    initial = models.FloatField(blank=True, null=True)
    min_value = models.FloatField(blank=True, null=True)
    max_value = models.FloatField(blank=True, null=True)

    FIELD_CLASS = 'django.forms.FloatField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniFloatField, self).as_form_field(
            min_value=self.min_value,
            max_value=self.max_value
        )


class OmniIntegerField(OmniField):
    """
    IntegerField representation
    """
    initial = models.IntegerField(blank=True, null=True)
    min_value = models.IntegerField(blank=True, null=True)
    max_value = models.IntegerField(blank=True, null=True)

    FIELD_CLASS = 'django.forms.IntegerField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniIntegerField, self).as_form_field(
            min_value=self.min_value,
            max_value=self.max_value
        )


class OmniTimeField(OmniField):
    """
    TimeField representation
    """
    initial = models.TimeField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.TimeField'
    FORM_WIDGETS = ('django.forms.widgets.TimeInput',)


class OmniUrlField(OmniField):
    """
    IntegerField representation
    """
    initial = models.URLField(blank=True, null=True)
    max_length = models.PositiveIntegerField(default=255, blank=True)
    min_length = models.PositiveIntegerField(default=0, blank=True)

    FIELD_CLASS = 'django.forms.URLField'
    FORM_WIDGETS = ('django.forms.widgets.URLInput',)

    def as_form_field(self, **kwargs):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :param kwargs: Extra keyword args to pass to the form field constructor
        :type kwargs: dict

        :return: django.forms.fields.Field subclass
        """
        return super(OmniUrlField, self).as_form_field(
            min_length=self.min_length,
            max_length=self.max_length
        )


class OmniRelatedField(OmniField):
    """
    Represents a field with relationships
    """
    related_type = models.ForeignKey(ContentType, related_name='+')
    initial = None

    def as_form_field(self):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :return: django.forms.fields.Field subclass
        """
        field_class = import_string(self.specific.FIELD_CLASS)
        widget_class = import_string(self.specific.widget_class)
        return field_class(
            queryset=self.related_type.model_class().objects.all(),
            widget=widget_class(),
            label=self.specific.label,
            help_text=self.specific.help_text,
            required=self.specific.required,
            initial=self.specific.initial
        )


class OmniManyToManyField(OmniRelatedField):
    """
    ManyToManyField representation
    """
    FIELD_CLASS = 'django.forms.ModelMultipleChoiceField'
    FORM_WIDGETS = ('django.forms.SelectMultiple', 'django.forms.CheckboxSelectMultiple')


class OmniForeignKeyField(OmniRelatedField):
    """
    ForeignKey field representation
    """
    FIELD_CLASS = 'django.forms.ModelChoiceField'
    FORM_WIDGETS = ('django.forms.Select', 'django.forms.RadioSelect')


@python_2_unicode_compatible
class OmniFormHandler(models.Model):
    """
    Base class for the form handler
    """
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    real_type = models.ForeignKey(ContentType, related_name='+')  # The Real OmniField type (set in the save method)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    form = GenericForeignKey()

    class Meta(object):
        """
        Django properties
        """
        ordering = ('order',)

    def __str__(self):
        """
        String representation of the model instance

        :return: The instance name
        """
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Custom save method
        Sets the actual content type on the instance if it doesn't exist already

        :param force_insert: Whether or not to force the insert
        :type force_insert: bool

        :param force_update: Whether or not to force the update
        :type force_update: bool

        :param using: Database connection to use
        :type using: connection

        :param update_fields: Fields to update
        :type update_fields: list

        :return: Saved instance
        """
        if not self.real_type_id:
            self.real_type = ContentType.objects.get_for_model(self)
        super(OmniFormHandler, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    @cached_property
    def specific(self):
        """
        Method for getting the most specific subclassed version of this instance

        :return: OmniField model subclass instance
        """
        real_type = self.real_type
        if isinstance(self, real_type.model_class()):
            return self
        else:
            return self.real_type.get_object_for_this_type(pk=self.pk)

    def handle(self, form):
        """
        Handle method stub

        :param form: Valid form instance
        :type form: django.forms.Form

        :raises: NotImplementedError
        """
        raise NotImplementedError('"{0}" must define it\'s own handle method'.format(self.__class__.__name__))

    def get_edit_url(self):
        """
        Generates a URL for editing the handler in the django admin

        :return: Edit URL for the admin interface
        """
        return reverse('admin:omniforms_omnimodelform_updatehandler', args=[self.object_id, self.pk])


@python_2_unicode_compatible
class TemplateHelpTextLazy(object):
    """
    Lazy object for generating help text for the
    OmniFormEmailHandler models 'template' field
    """
    def __init__(self, instance):
        """
        Sets up the instance

        :param instance: OmniFormEmailHandler model instance
        :type instance: OmniFormEmailHandler
        """
        super(TemplateHelpTextLazy, self).__init__()
        self.instance = instance

    def __str__(self):
        """
        Generates the string representation of the help text

        :return: Help text content
        """
        help_text = 'Please enter the content of the email here.'
        if self.instance.form:
            used_fields = self.instance.form.used_field_names
            if len(used_fields) > 0:
                help_text += ' Available tokens are {0}'.format(
                    ', '.join(['{{ %s }}' % field for field in used_fields])
                )
        return help_text


class OmniFormEmailHandler(OmniFormHandler):
    """
    Email handler for the form builder
    """
    subject = models.CharField(max_length=255)
    recipients = models.TextField()
    template = models.TextField()

    def __init__(self, *args, **kwargs):
        """
        Sets the help text for the 'template' field

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniFormEmailHandler, self).__init__(*args, **kwargs)
        self._meta.get_field('template').help_text = TemplateHelpTextLazy(self)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Send Email'

    def _render_template(self, context_data):
        """
        Renders the template data specified against the instance

        :param context_data: Context data for the email template
        :type context_data: dict

        :return: Rendered content
        """
        return Template(self.template).render(Context(context_data))

    @staticmethod
    def get_files(form):
        """
        Method for getting all uploaded files from the forms cleaned data

        :param form: Valid form instance
        :return: List of uploaded file instances
        """
        return list(
            filter(
                lambda value: isinstance(value, File),
                form.cleaned_data.values()
            )
        )

    def handle(self, form):
        """
        Handle method
        Sends an email to the specified recipients

        :param form: Valid form instance
        :type form: django.forms.Form
        """
        message = EmailMessage(
            self.subject,
            self._render_template(form.cleaned_data),
            settings.DEFAULT_FROM_EMAIL,
            self.recipients.split(',')
        )

        for file_object in self.get_files(form):
            message.attach(file_object.name, file_object.read(), file_object.content_type)

        message.send()


class OmniFormSaveInstanceHandler(OmniFormHandler):
    """
    Handler for saving the form instance
    """
    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Save Data'

    def assert_has_all_required_fields(self):
        """
        Property that determines whether or not the associated form defines all of the required fields

        :raises: ValidationError
        """
        defined_fields = self.form.used_field_names
        required_fields = self.form.get_required_field_names()
        missing_fields = []
        for field in required_fields:
            if field not in defined_fields:
                missing_fields.append(field)

        if len(missing_fields) > 0:
            raise ValidationError(
                'The save instance handler can only be attached to forms that contain fields for '
                'all required model fields.  The form you are attempting to attach this handler to '
                'is missing the following fields: ({0})'.format(', '.join(missing_fields))
            )

    def clean(self):
        """
        Cleans the handler for saving a model instance
        Ensures that the handler is attached to a model form instance

        :raises: ValidationError
        """
        super(OmniFormSaveInstanceHandler, self).clean()
        if not isinstance(self.form, OmniModelFormBase):
            raise ValidationError('This handler can only be attached to model forms')
        self.assert_has_all_required_fields()

    def handle(self, form):
        """
        Handle method
        Saves object instance to the database

        :param form: Valid form instance
        :type form: django.forms.Form
        """
        try:
            save_instance = import_string('django.forms.models.save_instance')
            commit = True

            if form.instance.pk is None:
                fail_message = 'created'
            else:
                fail_message = 'changed'

            save_instance(
                form, form.instance, form._meta.fields,
                fail_message, commit, form._meta.exclude,
                construct=False
            )
        except (ImportError, AttributeError):  # Django > 1.8
            form.instance.save()
            form._save_m2m()


class FormGeneratorMixin(object):
    """
    Mixin containing methods for form generation
    """
    def _get_form_class_name(self):
        """
        Method for generating a name for the form class

        :return: Name for the form class
        """
        return str('{0}{1}'.format(
            self.__class__.__name__,
            ''.join([fragment.capitalize() for fragment in re.split('\W+', self.title)])
        ))

    def _get_fields(self):
        """
        Method for getting all fields for the form class

        :return: list of form field instances
        """
        return [field.specific.as_form_field() for field in self.fields.all()]

    def _get_field(self, name):
        """
        Method for getting a field by its name

        :param name: Field name
        :type name: str|unicode

        :return: field instance
        """
        try:
            field = self.fields.get(name=name)
        except self.fields.model.DoesNotExist:
            return None
        else:
            return field.specific.as_form_field()

    def get_initial_data(self):
        """
        Method for getting the initial data for all fields on the form

        :return: Dict of initial data where the dict key is the field name
        """
        return {field.name: field.specific.initial for field in self.fields.all()}

    def _get_field_widgets(self):
        """
        Method for getting the widgets for all fields on the form

        :return: Dict of field widgets where the dict key is the field name
        """
        return {field.name: import_string(field.widget_class) for field in self.fields.all()}

    def _get_field_labels(self):
        """
        Method for getting the labels for all fields on the form

        :return: Dict of field labels where the dict key is the field name
        """
        return {field.name: field.label for field in self.fields.all()}

    def _get_field_help_texts(self):
        """
        Method for getting help text for all fields on the form

        :return: Dict of field widgets where the dict key is the field name
        """
        return {field.name: field.help_text for field in self.fields.all()}

    def get_form_class(self):
        """
        Method for generating a form class from the data contained within the model

        :return: ModelForm class
        """
        return type(
            self._get_form_class_name(),
            (forms.Form,),
            {'base_fields': self._get_fields()}
        )


@python_2_unicode_compatible
class OmniFormBase(FormGeneratorMixin, models.Model):
    """
    Base class for the OmniForm model
    """
    title = models.CharField(max_length=255)

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    def __str__(self):
        """
        Method for generating a string representation of the instance

        :return: String representation of the instance
        """
        return self.title


class OmniModelFormBase(OmniFormBase):
    """
    Base class for the OmniModelForm model
    """
    content_type = models.ForeignKey(ContentType, related_name='+')

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    def _get_base_form_class(self):
        """
        Helper method for getting the base ModelForm class for use with the model form factory

        :return: ModelForm instance
        """
        return type(
            self._get_form_class_name(),
            (OmniModelFormBaseForm,),
            {'_handlers': [handler.specific for handler in self.handlers.all()]}
        )

    def formfield_callback(self, model_field, **kwargs):
        """
        Custom formfield callback for the model form factory

        :param model_field: The model field to get a form field for
        :param kwargs: Default keyword args
        :return: Form field or None
        """
        return self._get_field(model_field.name)

    def get_form_class(self):
        """
        Method for generating a form class from the data contained within the model

        :return: ModelForm class
        """
        return modelform_factory(
            self.content_type.model_class(),
            form=self._get_base_form_class(),
            fields=self.used_field_names,
            formfield_callback=self.formfield_callback
        )

    @cached_property
    def used_field_names(self):
        """
        Property for getting the names of all fields associated with the form

        :return: List of available field names
        """
        return self.fields.values_list('name', flat=True)

    def get_model_fields(self):
        """
        Method to get all model fields for the content type
        associated with the forms specified content type

        :return: List of model field instances
        """

        def is_valid_field(field):
            if isinstance(field, (models.AutoField, ForeignObjectRel, GenericRelation, GenericForeignKey)):
                return False
            else:
                return True
        return list(filter(is_valid_field, self.content_type.model_class()._meta.get_fields()))

    def get_model_field_names(self):
        """
        Method to get all model field names for the content type
        associated with the forms specified content type

        :return: List of field name strings
        """
        return [field.name for field in self.get_model_fields()]

    def get_model_field_choices(self):
        """
        Method to get field choices for the admin addfield form

        :return: List of (field.name, field.verbose_name) choices for use in the admin form
        """
        return [
            (field.name, getattr(field, 'verbose_name', field.name))
            for field in self.get_model_fields()
            if field.name not in self.used_field_names
        ]

    def get_required_fields(self, exclude_with_default=True):
        """
        Method to get all required fields for the linked content type model

        :param exclude_with_default: Whether or not to exclude fields with default values
        :type exclude_with_default: bool

        :return: List of required field names
        """
        def filter_field(field):
            if field.blank:
                return False
            elif isinstance(field, models.ManyToManyField):
                return False
            elif exclude_with_default and field.has_default():
                return False
            else:
                return True
        return list(filter(filter_field, self.get_model_fields()))

    def get_required_field_names(self, exclude_with_default=True):
        """
        Method to get the names of all required fields for the linked content type model

        :return: List of required field names
        """
        return list(map(
            lambda field: field.name,
            self.get_required_fields(exclude_with_default=exclude_with_default)
        ))


class OmniForm(OmniFormBase):
    """
    Concrete implementation of the omni form
    """
    fields = GenericRelation(OmniField)
    handlers = GenericRelation(OmniFormHandler)


class OmniModelForm(OmniModelFormBase):
    """
    Concrete implementation of the omni model form
    """
    fields = GenericRelation(OmniField)
    handlers = GenericRelation(OmniFormHandler)
