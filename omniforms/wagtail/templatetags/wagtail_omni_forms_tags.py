"""
Custom template tags
"""
from django import template


register = template.Library()


WIDGET_CLASS_NAMES = {
    'CheckboxInput': ' boolean_field checkbox_input',
    'DateTimeInput': ' date_time_field admin_date_time_input',
    'DateInput': ' date_field admin_date_input',
    'TimeInput': ' time_field admin_time_input',
    'NumberInput': ' integer_field number_input',
    'Textarea': ' char_field admin_auto_height_text_input',
    'Select': ' typed_choice_field select',
}


@register.simple_tag
def admin_field_classes_for_field(form_field):
    """
    Helper class for generating and returning a list of classes
    appropriate for a given form field so that the fields in any
    custom admin view templates can be appropriately styled

    :param form_field: django form field instance
    :return: str - class names for a given form field wrapper
    """
    widget_class_name = form_field.field.widget.__class__.__name__
    extra_classes = WIDGET_CLASS_NAMES.get(widget_class_name, ' char_field')
    return 'field' + extra_classes


@register.simple_tag
def admin_field_classes_for_object(form_field):
    """
    Helper class for generating and returning a list of classes
    appropriate for a given form field so that the fields in any
    custom admin view templates can be appropriately styled

    :param form_field: django form field instance
    :return: str - class names for a given form field wrapper
    """
    classes = 'object'
    if form_field.field.required:
        classes += ' required'

    if form_field.errors:
        classes += ' error'

    widget_class_name = form_field.field.widget.__class__.__name__
    extra_classes = WIDGET_CLASS_NAMES.get(widget_class_name, ' char_field')
    return classes + extra_classes


@register.filter(name='widget_type')
def widget_type(field):
    """
    Template filter that returns field widget class name (in lower case).
    E.g. if field's widget is TextInput then {{ field|widget_type }} will
    return 'textinput'.
    This has been copied across from the wagtail_tweaks library as it was our
    sole reason for using it.
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget') and field.field.widget:
        return field.field.widget.__class__.__name__.lower()
    return ''
