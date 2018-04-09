from django import forms
from django.test import TestCase

from omniforms.models import OmniForm
from omniforms.tests.factories import (
    OmniFormFactory,
    OmniCharFieldFactory,
    OmniBooleanFieldFactory,
    OmniFormEmailHandlerFactory
)
from omniforms.wagtail.forms import WagtailOmniFormCloneForm


class WagtailOmniFormCloneFormTestCase(TestCase):
    """
    Tests the WagtailOmniFormCloneForm form class
    """
    def setUp(self):
        super(WagtailOmniFormCloneFormTestCase, self).setUp()
        self.instance = OmniFormFactory.create()
        self.field_1 = OmniCharFieldFactory.create(form=self.instance)
        self.field_2 = OmniBooleanFieldFactory.create(form=self.instance)
        self.handler_1 = OmniFormEmailHandlerFactory.create(form=self.instance)
        self.handler_2 = OmniFormEmailHandlerFactory.create(form=self.instance)
        self.form = WagtailOmniFormCloneForm(
            data={'title': 'Cloned'},
            instance=self.instance
        )

    def test_inheritance(self):
        """
        The form should be a model form
        """
        self.assertIsInstance(self.form, forms.ModelForm)

    def test_model(self):
        """
        The form should use the correct model class
        """
        self.assertEqual(self.form._meta.model, OmniForm)

    def test_form_initial_data(self):
        """
        The forms title should not contain initial data
        """
        self.assertIsNone(self.form.initial['title'])

    def test_clones_form(self):
        """
        The forms save method should clone the omni form
        """
        self.assertTrue(self.form.is_valid())
        instance = self.form.save()
        self.assertNotEqual(instance, self.instance)
        self.assertEqual(2, instance.fields.count())
        self.assertEqual(2, instance.handlers.count())

    def test_clones_form_fields(self):
        """
        The forms save method should clone the omni forms fields
        """
        self.assertTrue(self.form.is_valid())
        instance = self.form.save()

        field_1 = instance.fields.get(name=self.field_1.name)
        self.assertNotEqual(field_1, self.field_1)
        self.assertEqual(field_1.label, self.field_1.label)
        self.assertEqual(field_1.widget_class, self.field_1.widget_class)
        self.assertEqual(field_1.order, self.field_1.order)

        field_2 = instance.fields.get(name=self.field_2.name)
        self.assertNotEqual(field_2, self.field_2)
        self.assertEqual(field_2.label, self.field_2.label)
        self.assertEqual(field_2.widget_class, self.field_2.widget_class)
        self.assertEqual(field_2.order, self.field_2.order)

    def test_clones_form_handlers(self):
        """
        The forms save method should clone the omni forms handlers
        """
        self.assertTrue(self.form.is_valid())
        instance = self.form.save()

        handler_1 = instance.handlers.get(name=self.handler_1.name).specific
        self.assertNotEqual(handler_1, self.handler_1)
        self.assertEqual(handler_1.order, self.handler_1.order)
        self.assertEqual(handler_1.subject, self.handler_1.subject)
        self.assertEqual(handler_1.recipients, self.handler_1.recipients)
        self.assertEqual(handler_1.template, self.handler_1.template)

        handler_2 = instance.handlers.get(name=self.handler_2.name).specific
        self.assertNotEqual(handler_2, self.handler_2)
        self.assertEqual(handler_2.order, self.handler_2.order)
        self.assertEqual(handler_2.subject, self.handler_2.subject)
        self.assertEqual(handler_2.recipients, self.handler_2.recipients)
        self.assertEqual(handler_2.template, self.handler_2.template)
