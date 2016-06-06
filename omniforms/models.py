# -*- coding: utf-8 -*-
"""
Models for the omniforms app
"""
from __future__ import unicode_literals
from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
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
    real_type = models.ForeignKey(ContentType, related_name='+')
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
        String representation of the instance

        :return: Fields label
        """
        return self.label

    @classmethod
    def get_concrete_class_for_model_field(cls, model_field):
        """
        Method for getting a concrete model class to represent the type of form field required

        :param model_field: Model Field instance
        :type model_field: django.forms.Field

        :return: OmniField subclass
        """
        return {
            models.CharField: OmniCharField,
            models.BooleanField: OmniBooleanField,
            models.DateField: OmniDateField,
            models.DateTimeField: OmniDateTimeField,
            models.DecimalField: OmniDecimalField,
            models.EmailField: OmniEmailField,
            models.FloatField: OmniFloatField,
            models.IntegerField: OmniIntegerField,
            models.TimeField: OmniTimeField,
            models.URLField: OmniUrlField
        }.get(model_field.__class__)

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

    def as_form_field(self):
        """
        Method for generating a form field instance from the
        specified data stored against this model instance

        :return: django.forms.fields.Field subclass
        """
        field_class = import_string(self.specific.FIELD_CLASS)
        widget_class = import_string(self.specific.widget_class)
        return field_class(
            widget=widget_class(),
            label=self.specific.label,
            help_text=self.specific.help_text,
            required=self.specific.required,
            initial=self.specific.initial
        )


class OmniCharField(OmniField):
    """
    CharField representation
    """
    initial = models.TextField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.CharField'
    FORM_WIDGETS = (
        'django.forms.widgets.TextInput',
        'django.forms.widgets.Textarea',
        'django.forms.widgets.PasswordInput'
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
    initial = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    FIELD_CLASS = 'django.forms.DecimalField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)


class OmniEmailField(OmniField):
    """
    EmailField representation
    """
    initial = models.EmailField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.EmailField'
    FORM_WIDGETS = ('django.forms.widgets.EmailInput',)


class OmniFloatField(OmniField):
    """
    FloatField representation
    """
    initial = models.FloatField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.FloatField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)


class OmniIntegerField(OmniField):
    """
    IntegerField representation
    """
    initial = models.IntegerField(blank=True, null=True)
    FIELD_CLASS = 'django.forms.IntegerField'
    FORM_WIDGETS = ('django.forms.widgets.NumberInput',)


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
    FIELD_CLASS = 'django.forms.URLField'
    FORM_WIDGETS = ('django.forms.widgets.URLInput',)


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

    @staticmethod
    def _get_form_class_bases():
        """
        Method for getting a tuple of base classes for the form

        :return: Tuple of base classes for the form
        """
        return forms.Form,

    def _get_fields(self):
        """
        Method for getting all fields for the form class

        :return: list of form field instances
        """
        return [field.as_form_field() for field in self.fields.all()]

    def _get_field_names(self):
        return self.fields.values_list('name', flat=True)

    def _get_field_widgets(self):
        return {field.name: import_string(field.widget_class) for field in self.fields.all()}

    def _get_field_help_texts(self):
        return {field.name: field.help_text for field in self.fields.all()}

    def _get_form_class_properties(self):
        """
        Method for getting a dict of form properties

        :return: Dict of properties to set on the form class
        """
        return {'base_fields': self._get_fields()}

    def get_form_class(self):
        """
        Method for generating a form class from the data contained within the model

        :return: ModelForm class
        """
        return type(
            self._get_form_class_name(),
            self._get_form_class_bases(),
            self._get_form_class_properties()
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
    content_type = models.ForeignKey(ContentType, related_name='+', help_text='THis is some help text')

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    @staticmethod
    def _get_form_class_bases():
        """
        Method for getting a tuple of base classes for the form

        :return: Tuple of base classes for the form
        """
        return forms.ModelForm,

    def _get_form_meta_class(self):
        """
        Method for getting a meta class for the form

        :return: Tuple of base classes for the form
        """
        return type(str('Meta'), (object,), {
            'model': self.content_type.model_class(),
            'fields': self._get_field_names(),
            'widgets': self._get_field_widgets(),
            'help_texts': self._get_field_help_texts()
        })

    def _get_form_class_properties(self):
        """
        Method for getting a dict of form properties

        :return: Dict of properties to set on the form class
        """
        properties = super(OmniModelFormBase, self)._get_form_class_properties()
        properties['Meta'] = self._get_form_meta_class()
        return properties


class OmniForm(OmniFormBase):
    """
    Concrete implementation of the omni form
    """
    fields = GenericRelation(OmniField)


class OmniModelForm(OmniModelFormBase):
    """
    Concrete implementation of the omni model form
    """
    fields = GenericRelation(OmniField)
