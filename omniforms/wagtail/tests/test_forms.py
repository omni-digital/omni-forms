from mock import patch

from django import forms
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from omniforms.models import OmniForm, OmniField, OmniFormHandler
from omniforms.tests.factories import (
    OmniFormFactory,
    OmniCharFieldFactory,
    OmniBooleanFieldFactory,
    OmniFormEmailHandlerFactory
)
from omniforms.wagtail.forms import (
    WagtailOmniFormCloneForm,
    OmniPermissionFormBase,
    OmniFieldPermissionForm,
    OmniHandlerPermissionForm
)


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


class OmniPermissionFormBaseTestCase(TestCase):
    """
    Tests the OmniPermissionFormBase class
    """
    def setUp(self):
        super(OmniPermissionFormBaseTestCase, self).setUp()
        # Create a group and assign it a permission not managed by the forms we're testing
        self.add_form_permission = Permission.objects.get(codename='add_omniform')
        self.group = Group.objects.create(name='dummy')
        self.group.permissions.add(self.add_form_permission)
        self.group.save()

        self.form = OmniPermissionFormBase(instance=self.group)
        self.form.admin_panel_title = 'Dummy permissions'
        self.form.fields['permissions'].queryset = Permission.objects.filter(
            content_type__app_label='omniforms',
            content_type__model='omnicharfield'
        )

    def test_config(self):
        """
        The form should be configured correctly
        """
        self.assertTrue(issubclass(OmniPermissionFormBase, forms.ModelForm))
        self.assertEqual(OmniPermissionFormBase._meta.model, Group)
        self.assertIn('permissions', OmniPermissionFormBase().fields)

    def test_checkboxes_by_id(self):
        """
        The method should return the correct data
        """
        results = self.form._checkboxes_by_id(self.form['permissions'])
        self.assertEqual(len(results), self.form.fields['permissions'].queryset.count())
        for instance in self.form.fields['permissions'].queryset:
            self.assertIn(instance.pk, results)
            self.assertIsInstance(results[instance.pk], forms.boundfield.BoundWidget)
            self.assertIsInstance(results[instance.pk].parent_widget, forms.CheckboxSelectMultiple)

    @patch('omniforms.wagtail.forms.render_to_string')
    def test_as_admin_panel(self, render_to_string):
        """
        The method should render the template with the correct data
        """
        render_to_string.return_value = 'Rendered content'
        rendered = self.form.as_admin_panel()
        self.assertEqual(rendered, render_to_string.return_value)

        template = render_to_string.mock_calls[0][1][0]
        context = render_to_string.mock_calls[0][1][1]

        self.assertEqual(template, 'modeladmin/omniforms/wagtail/includes/permissions.html')
        self.assertEqual(context['title'], 'Dummy permissions')
        self.assertEqual(1, len(context['object_perms']))
        self.assertEqual('Char Field', context['object_perms'][0]['object'])
        self.assertIsInstance(context['object_perms'][0]['add'], forms.boundfield.BoundWidget)
        self.assertIsInstance(context['object_perms'][0]['add'].parent_widget, forms.CheckboxSelectMultiple)
        self.assertEqual(
            context['object_perms'][0]['add'].data['value'],
            Permission.objects.get(codename='add_omnicharfield').pk
        )
        self.assertIsInstance(context['object_perms'][0]['change'], forms.boundfield.BoundWidget)
        self.assertIsInstance(context['object_perms'][0]['change'].parent_widget, forms.CheckboxSelectMultiple)
        self.assertEqual(
            context['object_perms'][0]['change'].data['value'],
            Permission.objects.get(codename='change_omnicharfield').pk
        )
        self.assertIsInstance(context['object_perms'][0]['delete'], forms.boundfield.BoundWidget)
        self.assertIsInstance(context['object_perms'][0]['delete'].parent_widget, forms.CheckboxSelectMultiple)
        self.assertEqual(
            context['object_perms'][0]['delete'].data['value'],
            Permission.objects.get(codename='delete_omnicharfield').pk
        )

    def test_save_adds_permissions(self):
        """
        The save method should add the selected permissions whilst leaving permissions not managed by the form alone
        """
        add_charfield_permission = Permission.objects.get(codename='add_omnicharfield')
        form = OmniPermissionFormBase(
            instance=self.group,
            data={'permissions': [add_charfield_permission.pk]}
        )
        form.fields['permissions'].queryset = Permission.objects.filter(
            content_type__app_label='omniforms',
            content_type__model='omnicharfield'
        )
        form.full_clean()
        form.save()

        self.group.refresh_from_db()
        # Make sure the non managed permission has not been removed accidentally
        self.assertIn(self.add_form_permission, self.group.permissions.all())
        # Ensure that the new permission has been added
        self.assertIn(add_charfield_permission, self.group.permissions.all())

    def test_save_removes_permissions(self):
        """
        The save method should remove existing permissions whilst leaving permissions not managed by the form alone
        """
        add_charfield_permission = Permission.objects.get(codename='add_omnicharfield')
        self.group.permissions.add(add_charfield_permission)
        self.group.save()
        form = OmniPermissionFormBase(instance=self.group, data={'permissions': []})
        form.fields['permissions'].queryset = Permission.objects.filter(
            content_type__app_label='omniforms',
            content_type__model='omnicharfield'
        )
        form.full_clean()
        form.save()

        self.group.refresh_from_db()
        # Make sure the non managed permission has not been removed accidentally
        self.assertIn(self.add_form_permission, self.group.permissions.all())
        # Ensure that the new permission has been added
        self.assertNotIn(add_charfield_permission, self.group.permissions.all())


class OmniFieldPermissionFormTestCase(TestCase):
    """
    Tests the OmniFieldPermissionForm
    """
    def test_config(self):
        """
        The form should be configured correctly
        """
        self.assertTrue(issubclass(OmniFieldPermissionForm, OmniPermissionFormBase))
        self.assertEqual(OmniFieldPermissionForm._meta.model, Group)
        self.assertIn('permissions', OmniFieldPermissionForm().fields)
        self.assertEqual(OmniFieldPermissionForm.admin_panel_title, 'OmniForm Fields')
        self.assertEqual(OmniFieldPermissionForm.prefix, 'omnifield_permission')

    def test_permission_queryset(self):
        """
        The permission fields queryset should contain the correct permissions
        """
        for instance in OmniFieldPermissionForm().fields['permissions'].queryset:
            model_class = instance.content_type.model_class()
            self.assertTrue(issubclass(model_class, OmniField))
            self.assertNotEqual(model_class, OmniField)


class OmniHandlerPermissionFormTestCase(TestCase):
    """
    Tests the OmniHandlerPermissionForm
    """
    def test_config(self):
        """
        The form should be configured correctly
        """
        self.assertTrue(issubclass(OmniHandlerPermissionForm, OmniPermissionFormBase))
        self.assertEqual(OmniHandlerPermissionForm._meta.model, Group)
        self.assertIn('permissions', OmniHandlerPermissionForm().fields)
        self.assertEqual(OmniHandlerPermissionForm.admin_panel_title, 'OmniForm Handlers')
        self.assertEqual(OmniHandlerPermissionForm.prefix, 'omnihandler_permission')

    def test_permission_queryset(self):
        """
        The permission fields queryset should contain the correct permissions
        """
        for instance in OmniHandlerPermissionForm().fields['permissions'].queryset:
            model_class = instance.content_type.model_class()
            self.assertTrue(issubclass(model_class, OmniFormHandler))
            self.assertNotEqual(model_class, OmniFormHandler)
