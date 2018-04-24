# -*- coding: utf-8 -*-
"""
Models for the omniforms app
"""
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.files import File
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.fields.related import ForeignObjectRel
from django.forms import modelform_factory
from django.template import Template, Context
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from omniforms.forms import OmniFormBaseForm, OmniModelFormBaseForm, EmailConfirmationHandlerBaseFormClass
import re


class OmniFormRelatedQuerySet(models.QuerySet):
    """
    Custom queryset for OmniFormHandler model
    """
    def _get_concrete_models(self, base_model_class):
        """
        Method for retrieving and returning a list of all handler model classes
        that are not either abstract classes or the base OmniFormHandler class

        :return: List of OmniFormHandler model classes
        """
        model_classes = []
        for ctype in ContentType.objects.all():
            model_class = ctype.model_class()
            if not model_class:
                continue

            if model_class._meta.abstract:
                continue

            if model_class == base_model_class or not issubclass(model_class, base_model_class):
                continue

            model_classes.append(model_class)
        return model_classes


class OmniFieldQuerySet(OmniFormRelatedQuerySet):
    """
    Custom QuerySet class for the OmniField model
    """
    def get_concrete_models(self):
        """
        Method for retrtieving and returning a list of all field model classes
        that are not either abstract classes or the base OmniField class

        :return: List of OmniField model classes
        """
        return self._get_concrete_models(OmniField)


class OmniFormHandlerQuerySet(OmniFormRelatedQuerySet):
    """
    Custom queryset for OmniFormHandler model
    """
    def get_concrete_models(self):
        """
        Method for retrieving and returning a list of all handler model classes
        that are not either abstract classes or the base OmniFormHandler class

        :return: List of OmniFormHandler model classes
        """
        return self._get_concrete_models(OmniFormHandler)


@python_2_unicode_compatible
class OmniField(models.Model):
    """
    Base class for omni fields
    """
    name = models.CharField(
        max_length=255,
        validators=[RegexValidator(
            regex='^[a-z0-9_]+$',
            message=_('The name may only contain alphanumeric characters and underscores.'),
            code='invalid_field_name'
        )],
        help_text=_(
            'The name of this field. May only contain alphanumeric characters '
            'and underscores. Must start and end with an alphanumeric character.'
        )
    )
    label = models.CharField(
        max_length=255,
        help_text=_(
            'Appears next to the form field and should identify it\'s purpose. '
            'Example, for an email field this could be \'Email address\''
        )
    )
    help_text = models.TextField(
        blank=True,
        null=True,
        help_text=_(
            'Provide any information that may assist users in '
            'filling out this form field here'
        )
    )
    required = models.BooleanField(
        default=False,
        help_text=_(
            'If checked, users must provide data within this field. '
            'If not checked the field is optional'
        )
    )
    widget_class = models.CharField(
        max_length=255,
        help_text=_('Determines how the field is displayed in the generated form')
    )
    order = models.IntegerField(
        default=0,
        help_text=_(
            'Determines where this field appears relative to other fields in the form. Smaller values '
            'cause the field to float to the top of the form, larger numbers cause the field to sink '
            'to the bottom of the form'
        )
    )
    real_type = models.ForeignKey(ContentType, related_name='+')  # The Real OmniField type (set in the save method)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    form = GenericForeignKey()

    objects = OmniFieldQuerySet.as_manager()

    class Meta(object):
        """
        Django properties
        """
        ordering = ('order',)
        unique_together = ('name', 'content_type', 'object_id')
        verbose_name = 'Field'

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
            initial=self.specific.initial_data,
            **kwargs
        )

    def get_edit_url(self):
        """
        Generates a URL for editing the field in the django admin

        :return: Edit URL for the admin interface
        """
        if isinstance(self.form, OmniModelForm):
            return reverse('admin:omniforms_omnimodelform_updatefield', args=[self.object_id, self.name])

        return reverse(
            'admin:omniforms_omniform_updatefield',
            args=[self.object_id, self.real_type_id, self.name]
        )


class OmniCharField(OmniField):
    """
    CharField representation
    """
    initial_data = models.TextField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    max_length = models.PositiveIntegerField(
        default=255,
        blank=True,
        help_text=_('The maximum amount of data that can be entered into this field')
    )
    min_length = models.PositiveIntegerField(
        default=0,
        blank=True,
        help_text=_('The minimum amount of data that can be entered into this field')
    )

    FIELD_CLASS = 'django.forms.CharField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.Textarea',
        'django.forms.widgets.PasswordInput'
    )

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Char Field'

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
    initial_data = models.DurationField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.DurationField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.Textarea'
    )

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Duration Field'


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

    initial_data = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    protocol = models.CharField(
        max_length=4,
        blank=True,
        choices=PROTOCOL_CHOICES,
        default=PROTOCOL_BOTH,
        help_text=_('Please select which protocol data entered into this field must adhere to')
    )
    unpack_ipv4 = models.BooleanField(
        default=False,
        blank=True,
        help_text=_('If checked IPV4 addresses will be unpacked')
    )

    FIELD_CLASS = 'django.forms.GenericIPAddressField'
    FORM_WIDGETS = ('django.forms.widgets.TextInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'IP Address Field'

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
    initial_data = models.UUIDField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.UUIDField'
    FORM_WIDGETS = ('django.forms.widgets.TextInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'UUID Field'


class OmniSlugField(OmniField):
    """
    SlugField representation
    """
    initial_data = models.SlugField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.SlugField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.HiddenInput'
    )

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Slug Field'


class OmniBooleanField(OmniField):
    """
    BooleanField representation
    """
    initial_data = models.NullBooleanField(
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.BooleanField'
    FORM_WIDGETS = ('django.forms.widgets.CheckboxInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Boolean Field'


class OmniDateField(OmniField):
    """
    DateField representation
    """
    initial_data = models.DateField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.DateField'
    FORM_WIDGETS = ('django.forms.widgets.DateInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Date Field'


class OmniDateTimeField(OmniField):
    """
    DateTimeField representation
    """
    initial_data = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.DateTimeField'
    FORM_WIDGETS = ('django.forms.widgets.DateTimeInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'DateTime Field'


class OmniDecimalField(OmniField):
    """
    DecimalField representation
    """
    initial_data = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=100,
        max_digits=1000,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    min_value = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=100,
        max_digits=1000,
        help_text=_('The minimum value that may be entered into this field')
    )
    max_value = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=100,
        max_digits=1000,
        help_text=_('The maximum value that may be entered into this field')
    )
    max_digits = models.PositiveIntegerField(
        help_text=_('The maximum number of digits that may be entered into this field')
    )
    decimal_places = models.PositiveIntegerField(
        help_text=_('The expected number of decimal places that must be entered into this field')
    )

    FIELD_CLASS = 'django.forms.DecimalField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Decimal Field'

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
    initial_data = models.EmailField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    max_length = models.PositiveIntegerField(
        default=255,
        blank=True,
        help_text=_('The maximum amount of data that can be entered into this field')
    )
    min_length = models.PositiveIntegerField(
        default=0,
        blank=True,
        help_text=_('The minimum amount of data that can be entered into this field')
    )

    FIELD_CLASS = 'django.forms.EmailField'
    FORM_WIDGETS = ('django.forms.widgets.EmailInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Email Field'

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
    initial_data = None
    max_length = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_('The maximum amount of data that can be entered into this field')
    )
    allow_empty_file = models.BooleanField(
        default=False,
        help_text=_(
            'If checked empty files may be uploaded using this field. '
            'Otherwise uploaded files may not be empty'
        )
    )

    FIELD_CLASS = 'django.forms.FileField'
    FORM_WIDGETS = ('django.forms.widgets.FileInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'File Field'

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
    initial_data = None
    FIELD_CLASS = 'django.forms.ImageField'
    FORM_WIDGETS = ('django.forms.widgets.FileInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Image Field'


class OmniFloatField(OmniField):
    """
    FloatField representation
    """
    initial_data = models.FloatField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    min_value = models.FloatField(
        blank=True,
        null=True,
        help_text=_('The minimum value that may be entered into this field')
    )
    max_value = models.FloatField(
        blank=True,
        null=True,
        help_text=_('The maximum value that may be entered into this field')
    )

    FIELD_CLASS = 'django.forms.FloatField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Float Field'

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
    initial_data = models.IntegerField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    min_value = models.IntegerField(
        blank=True,
        null=True,
        help_text=_('The minimum value that may be entered into this field')
    )
    max_value = models.IntegerField(
        blank=True,
        null=True,
        help_text=_('The maximum value that may be entered into this field')
    )

    FIELD_CLASS = 'django.forms.IntegerField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Integer Field'

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
    initial_data = models.TimeField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    FIELD_CLASS = 'django.forms.TimeField'
    FORM_WIDGETS = ('django.forms.widgets.TimeInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Time Field'


class OmniUrlField(OmniField):
    """
    IntegerField representation
    """
    initial_data = models.URLField(
        blank=True,
        null=True,
        help_text=_('If provided, initial data will appear in this field by default.')
    )
    max_length = models.PositiveIntegerField(
        default=255,
        blank=True,
        help_text=_('The maximum amount of data that can be entered into this field')
    )
    min_length = models.PositiveIntegerField(
        default=0,
        blank=True,
        help_text=_('The minimum amount of data that can be entered into this field')
    )

    FIELD_CLASS = 'django.forms.URLField'
    FORM_WIDGETS = ('django.forms.widgets.URLInput',)

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'URL Field'

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
    initial_data = None

    class Meta(object):
        abstract = True

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
            initial=self.specific.initial_data
        )


class OmniManyToManyField(OmniRelatedField):
    """
    ManyToManyField representation
    """
    FIELD_CLASS = 'django.forms.ModelMultipleChoiceField'
    FORM_WIDGETS = ('django.forms.SelectMultiple', 'django.forms.CheckboxSelectMultiple')

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Many To Many Field'


class OmniForeignKeyField(OmniRelatedField):
    """
    ForeignKey field representation
    """
    FIELD_CLASS = 'django.forms.ModelChoiceField'
    FORM_WIDGETS = ('django.forms.Select', 'django.forms.RadioSelect')

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Foreign Key Field'


class ChoiceFieldMixin(models.Model):
    """
    Provides common functionality for choice fields
    """
    initial_data = None
    choices = models.TextField(
        help_text='Please add one choice per line.'
    )

    class Meta(object):
        """
        Django model properties
        """
        abstract = True

    def _get_field_choices(self):
        """
        Generates a list of form field choices from the choices field data

        :return: List of form field choices
        """
        choices = []
        for choice in self.choices.splitlines():
            choice = choice.strip()
            if not choice:
                continue
            choices.append([choice, choice])
        return choices

    def as_form_field(self, **kwargs):
        """
        Adds the field choices to the field constructor kwargs
        before calling super and passing the choice along as well

        :param kwargs: Default keyword args
        :return: field instance
        """
        kwargs['choices'] = self._get_field_choices()
        return super(ChoiceFieldMixin, self).as_form_field(**kwargs)


class OmniChoiceField(ChoiceFieldMixin, OmniField):
    """
    Custom choice field type for the omni form
    """
    FIELD_CLASS = 'django.forms.ChoiceField'
    FORM_WIDGETS = (
        'django.forms.widgets.Select',
        'django.forms.widgets.RadioSelect'
    )

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Choice Field'


class OmniMultipleChoiceField(ChoiceFieldMixin, OmniField):
    """
    Custom multiple choice field type for the omni form
    """
    FIELD_CLASS = 'django.forms.MultipleChoiceField'
    FORM_WIDGETS = (
        'django.forms.widgets.SelectMultiple',
        'django.forms.widgets.CheckboxSelectMultiple'
    )

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Multiple Choice Field'


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

    objects = OmniFormHandlerQuerySet.as_manager()

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
        if isinstance(self.form, OmniModelForm):
            return reverse('admin:omniforms_omnimodelform_updatehandler', args=[self.object_id, self.pk])
        return reverse('admin:omniforms_omniform_updatehandler', args=[self.object_id, self.pk])


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


class OmniFormEmailHandlerBase(OmniFormHandler):
    """
    Base model class for email handlers
    """
    subject = models.CharField(
        max_length=255,
        help_text='The subject of the email that will be sent'
    )
    template = models.TextField()

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    def __init__(self, *args, **kwargs):
        """
        Sets the help text for the 'template' field

        :param args: Default positional args
        :type args: ()

        :param kwargs: Default keyword args
        :type kwargs: {}
        """
        super(OmniFormEmailHandlerBase, self).__init__(*args, **kwargs)
        self._meta.get_field('template').help_text = TemplateHelpTextLazy(self)

    def _get_recipients(self, form):
        raise NotImplementedError(
            "{0} must implement its own '_get_recipients' "
            "method".format(self.__class__.__name__)
        )

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
            self._get_recipients(form)
        )

        for file_object in self.get_files(form):
            message.attach(file_object.name, file_object.read(), file_object.content_type)

        message.send()


class OmniFormEmailHandler(OmniFormEmailHandlerBase):
    """
    Email handler for the form builder
    """
    recipients = models.TextField()

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Send Static Email'

    def _get_recipients(self, form):
        """
        Returns a list of recipient email addresses

        :param form: Valid form instance
        :return: list of email recipient addresses
        """
        return [recipient.strip() for recipient in self.recipients.split(',')]


class OmniFormEmailConfirmationHandler(OmniFormEmailHandlerBase):
    """
    Form handler for sending a confirmation email to the person who filled out the form
    """
    recipient_field = models.ForeignKey(
        'omniforms.OmniEmailField',
        on_delete=models.PROTECT,
        help_text='The field on the associated form used for collecting the users '
                  'email address. Note that if this field is optional and not filled '
                  'in by the user the confirmation email will not be sent'
    )

    base_form_class = EmailConfirmationHandlerBaseFormClass

    class Meta(object):
        """
        Django properties
        """
        verbose_name = 'Send Email Confirmation'

    def _get_recipients(self, form):
        """
        Returns a list containing the email address from the
        specified field in the submitted form data

        :param form: Valid form instance
        :return: list containing the intended recipient of the email
        """
        return [form.cleaned_data.get(self.recipient_field.name)]


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
        return {field.name: field.specific.as_form_field() for field in self.fields.all()}

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
        return {field.name: field.specific.initial_data for field in self.fields.all()}

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

    @property
    def used_field_names(self):
        """
        Property for getting the names of all fields associated with the form

        :return: List of available field names
        """
        return self.fields.values_list('name', flat=True)


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

    def _get_base_form_class(self):
        """
        Helper method for getting the base ModelForm class for use with the model form factory

        :return: ModelForm instance
        """
        return type(
            self._get_form_class_name(),
            (OmniFormBaseForm,),
            {'_handlers': [handler.specific for handler in self.handlers.all()]}
        )

    def get_form_class(self):
        """
        Method for generating a form class from the data contained within the model

        :return: ModelForm class
        """
        return type(
            self._get_form_class_name(),
            (self._get_base_form_class(),),
            self._get_fields()
        )


class OmniModelForm(OmniModelFormBase):
    """
    Concrete implementation of the omni model form
    """
    fields = GenericRelation(OmniField)
    handlers = GenericRelation(OmniFormHandler)

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
