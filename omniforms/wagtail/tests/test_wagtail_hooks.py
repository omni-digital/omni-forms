from mock import Mock, patch

from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from wagtail.contrib.modeladmin.helpers.button import ButtonHelper
from wagtail.contrib.modeladmin.helpers.permission import PermissionHelper
from wagtail.contrib.modeladmin.helpers.url import AdminURLHelper
from wagtail.contrib.modeladmin.options import ModelAdmin

from omniforms.models import OmniForm
from omniforms.wagtail.wagtail_hooks import (
    add_omniforms_permissions,
    WagtailOmniFormModelAdmin,
    WagtailOmniFormButtonHelper,
    WagtailOmniFormURLHelper,
    WagtailOmniFormPermissionHelper
)
from omniforms.tests.factories import UserFactory


class AddOmniformsPermissionsTestCase(TestCase):
    """
    Tests the add_omniforms_permissions wagtail hook
    """
    def test_returns_correct_permissions(self):
        """
        The function should return the correct permissions
        """
        add_permission = Permission.objects.get(codename='add_omniform')
        change_permission = Permission.objects.get(codename='change_omniform')
        delete_permission = Permission.objects.get(codename='delete_omniform')

        permissions = add_omniforms_permissions()
        self.assertEqual(3, permissions.count())
        self.assertIn(add_permission, permissions)
        self.assertIn(change_permission, permissions)
        self.assertIn(delete_permission, permissions)


class WagtailOmniFormURLHelperTestCase(TestCase):
    """
    Tests the WagtailOmniFormURLHelper
    """
    def setUp(self):
        super(WagtailOmniFormURLHelperTestCase, self).setUp()
        self.helper = WagtailOmniFormURLHelper(OmniForm)

    def test_inheritance(self):
        """
        The class should inherit from the correct base class
        """
        self.assertTrue(issubclass(WagtailOmniFormURLHelper, AdminURLHelper))

    def test_get_action_url_pattern_clone_form(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('clone_form'),
            r'^omniforms/omniform/clone_form/(?P<instance_pk>[-\w]+)/$'
        )

    def test_get_action_url_pattern_add_field(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('add_field'),
            r'^omniforms/omniform/add_field/(?P<instance_pk>[-\w]+)/(?P<related_object_ctype_id>[\d]+)/$'
        )

    def test_get_action_url_pattern_change_field(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('change_field'),
            r'^omniforms/omniform/change_field/(?P<instance_pk>[-\w]+)/(?P<related_object_id>[\d]+)/$'
        )

    def test_get_action_url_pattern_delete_field(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('delete_field'),
            r'^omniforms/omniform/delete_field/(?P<instance_pk>[-\w]+)/(?P<related_object_id>[\d]+)/$'
        )

    def test_get_action_url_pattern_add_handler(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('add_handler'),
            r'^omniforms/omniform/add_handler/(?P<instance_pk>[-\w]+)/(?P<related_object_ctype_id>[\d]+)/$'
        )

    def test_get_action_url_pattern_change_handler(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('change_handler'),
            r'^omniforms/omniform/change_handler/(?P<instance_pk>[-\w]+)/(?P<related_object_id>[\d]+)/$'
        )

    def test_get_action_url_pattern_delete_handler(self):
        """
        The method should return the correct regex
        """
        self.assertEqual(
            self.helper.get_action_url_pattern('delete_handler'),
            r'^omniforms/omniform/delete_handler/(?P<instance_pk>[-\w]+)/(?P<related_object_id>[\d]+)/$'
        )


class WagtailOmniFormModelAdminTestCase(TestCase):
    """
    Tests the WagtailOmniFormModelAdmin
    """
    def test_inheritance(self):
        """
        The class should inherit from wagtail.contrib.modeladmin.options.ModelAdmin
        """
        self.assertTrue(issubclass(WagtailOmniFormModelAdmin, ModelAdmin))

    def test_model(self):
        """
        The class should use the correct model
        """
        self.assertEqual(
            WagtailOmniFormModelAdmin.model,
            OmniForm
        )

    def test_menu_label(self):
        """
        The class should define an appropriate menu label
        """
        self.assertEqual(
            WagtailOmniFormModelAdmin.menu_label,
            'Omni forms'
        )

    def test_menu_icon(self):
        """
        The class should define an appropriate menu icon
        """
        self.assertEqual(
            WagtailOmniFormModelAdmin.menu_icon,
            'form'
        )

    def test_visibility(self):
        """
        The model should not appear in the settings menu or the explorer
        """
        self.assertFalse(WagtailOmniFormModelAdmin.add_to_settings_menu)
        self.assertTrue(WagtailOmniFormModelAdmin.exclude_from_explorer)

    def test_list_display(self):
        """
        The appropriate fields should be displayed
        """
        self.assertIn('title', WagtailOmniFormModelAdmin.list_display)
        self.assertIn('omni_form_fields', WagtailOmniFormModelAdmin.list_display)
        self.assertIn('omni_form_handlers', WagtailOmniFormModelAdmin.list_display)
        self.assertIn('omni_form_locked', WagtailOmniFormModelAdmin.list_display)

    def test_search_fields(self):
        """
        The appropriate fields should be searchable
        """
        self.assertIn('title', WagtailOmniFormModelAdmin.search_fields)

    def test_excluded_form_fields(self):
        """
        The appropriate fields should be excluded from the add/edit form
        """
        self.assertIn('fields', WagtailOmniFormModelAdmin.form_fields_exclude)
        self.assertIn('handlers', WagtailOmniFormModelAdmin.form_fields_exclude)

    def test_button_helper_class(self):
        """
        The ModelAdmin should use the correct button_helper_class
        """
        self.assertEqual(
            WagtailOmniFormModelAdmin.button_helper_class,
            WagtailOmniFormButtonHelper
        )

    def test_url_helper_class(self):
        """
        The ModelAdmin should use the correct url_helper_class
        """
        self.assertEqual(
            WagtailOmniFormModelAdmin.url_helper_class,
            WagtailOmniFormURLHelper
        )

    def test_permission_helper_class(self):
        """
        The ModelAdmin should use the correct permission_helper_class
        """
        self.assertEqual(
            WagtailOmniFormModelAdmin.permission_helper_class,
            WagtailOmniFormPermissionHelper
        )


class WagtailOmniFormButtonHelperTestCase(TestCase):
    """
    Tests the WagtailOmniFormButtonHelper
    """
    def test_inheritance(self):
        """
        The model should inherit from the class
        """
        self.assertTrue(issubclass(WagtailOmniFormButtonHelper, ButtonHelper))

    def test_get_buttons_for_obj(self):
        """
        The method should add a button for adding a field to the form
        """
        request = RequestFactory().get('/dummy-path/')
        request.user = UserFactory.create(
            is_staff=True,
            is_superuser=True
        )

        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin.index_view_class(model_admin)
        instance = OmniForm.objects.create(title='Dummy Form')
        helper = WagtailOmniFormButtonHelper(view, request)
        buttons = helper.get_buttons_for_obj(instance)

        self.assertIn({
            'url': helper.url_helper.get_action_url('select_field', instance.pk),
            'label': 'Add field',
            'classname': helper.finalise_classname(helper.edit_button_classnames),
            'title': 'Add a new field',
        }, buttons)
        self.assertIn({
            'url': helper.url_helper.get_action_url('select_handler', instance.pk),
            'label': 'Add handler',
            'classname': helper.finalise_classname(helper.edit_button_classnames),
            'title': 'Add a new handler',
        }, buttons)
        self.assertIn({
            'url': helper.url_helper.get_action_url('clone_form', instance.pk),
            'label': 'Clone form',
            'classname': helper.finalise_classname(helper.edit_button_classnames),
            'title': 'Clone form',
        }, buttons)

    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_get_buttons_for_obj_add_field_missing(self, user_can_edit_obj):
        """
        The method should not add a button for adding a field to the form if the form cannot be edited
        """
        user_can_edit_obj.return_value = False
        request = RequestFactory().get('/dummy-path/')
        request.user = UserFactory.create(
            is_staff=True,
            is_superuser=True
        )

        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin.index_view_class(model_admin)
        instance = OmniForm.objects.create(title='Dummy Form')
        helper = WagtailOmniFormButtonHelper(view, request)
        buttons = helper.get_buttons_for_obj(instance)

        self.assertNotIn({
            'url': helper.url_helper.get_action_url('select_field', instance.pk),
            'label': 'Add field',
            'classname': helper.finalise_classname(helper.edit_button_classnames),
            'title': 'Add a new field',
        }, buttons)

    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_get_buttons_for_obj_add_handler_missing(self, user_can_edit_obj):
        """
        The method should not add a button for adding a handler to the form if the form cannot be edited
        """
        user_can_edit_obj.return_value = False
        request = RequestFactory().get('/dummy-path/')
        request.user = UserFactory.create(
            is_staff=True,
            is_superuser=True
        )

        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin.index_view_class(model_admin)
        instance = OmniForm.objects.create(title='Dummy Form')
        helper = WagtailOmniFormButtonHelper(view, request)
        buttons = helper.get_buttons_for_obj(instance)

        self.assertNotIn({
            'url': helper.url_helper.get_action_url('select_handler', instance.pk),
            'label': 'Add handler',
            'classname': helper.finalise_classname(helper.edit_button_classnames),
            'title': 'Add a new handler',
        }, buttons)


class WagtailOmniFormPermissionHelperTestCase(TestCase):
    """
    Tests the WagtailOmniFormPermissionHelper
    """
    def setUp(self):
        super(WagtailOmniFormPermissionHelperTestCase, self).setUp()
        self.user = UserFactory.create(
            is_staff=True,
            is_superuser=False
        )
        self.add_permission = Permission.objects.get(codename='add_omniform')
        self.change_permission = Permission.objects.get(codename='change_omniform')
        self.delete_permission = Permission.objects.get(codename='delete_omniform')
        self.form = OmniForm.objects.create(title='Form')
        self.permission_helper = WagtailOmniFormPermissionHelper(OmniForm)

    def test_inheritance(self):
        """
        The model should inherit from the class
        """
        self.assertTrue(issubclass(WagtailOmniFormPermissionHelper, PermissionHelper))

    def test_user_can_edit_obj_true(self):
        """
        The user should be able to edit the form
        """
        self.user.user_permissions.add(self.change_permission)
        self.assertTrue(self.permission_helper.user_can_edit_obj(self.user, self.form))

    def test_user_can_edit_obj_false_without_permission(self):
        """
        The user should not be able to edit the form without the appropriate permission
        """
        self.assertFalse(self.permission_helper.user_can_edit_obj(self.user, self.form))

    @patch('omniforms.wagtail.wagtail_hooks.hooks.get_hooks')
    def test_user_can_edit_obj_false_with_permission_error(self, get_hooks):
        """
        The user should not be able to edit the form if an omniform_permission_check hook raises permission error
        """
        dummy_hook = Mock(side_effect=PermissionDenied)
        get_hooks.return_value = [dummy_hook]
        self.assertFalse(self.permission_helper.user_can_edit_obj(self.user, self.form))

    def test_user_can_delete_obj_true(self):
        """
        The user should be able to delete the form
        """
        self.user.user_permissions.add(self.delete_permission)
        self.assertTrue(self.permission_helper.user_can_delete_obj(self.user, self.form))

    def test_user_can_delete_obj_false_without_permission(self):
        """
        The user should not be able to delete the form without the appropriate permission
        """
        self.assertFalse(self.permission_helper.user_can_delete_obj(self.user, self.form))

    @patch('omniforms.wagtail.wagtail_hooks.hooks.get_hooks')
    def test_user_can_delete_obj_false_with_permission_error(self, get_hooks):
        """
        The user should not be able to delete the form if an omniform_permission_check hook raises permission error
        """
        dummy_hook = Mock(side_effect=PermissionDenied)
        get_hooks.return_value = [dummy_hook]
        self.assertFalse(self.permission_helper.user_can_delete_obj(self.user, self.form))

    def test_user_can_clone_obj_true(self):
        """
        The user should be able to clone the form
        """
        self.user.user_permissions.add(self.add_permission)
        self.assertTrue(self.permission_helper.user_can_clone_obj(self.user, self.form))

    def test_user_can_clone_obj_false_without_permission(self):
        """
        The user should not be able to clone the form without the appropriate permission
        """
        self.assertFalse(self.permission_helper.user_can_clone_obj(self.user, self.form))

    @patch('omniforms.wagtail.wagtail_hooks.hooks.get_hooks')
    def test_user_can_clone_obj_false_with_permission_error(self, get_hooks):
        """
        The user should not be able to delete the form if an omniform_permission_check hook raises permission error
        """
        dummy_hook = Mock(side_effect=PermissionDenied)
        get_hooks.return_value = [dummy_hook]
        self.assertFalse(self.permission_helper.user_can_clone_obj(self.user, self.form))


class FieldControlsRenderingTestCase(TestCase):
    """
    Tests the rendering of the field controls
    """
    def test_renders_paragraph_without_edit_or_delete_urls(self):
        """
        The template should just render a paragraph
        """
        rendered = render_to_string(
            'modeladmin/omniforms/wagtail/includes/related_controls.html',
            {
                'button_text': 'Some field',
                'edit_url': None,
                'delete_url': None,
                'form_locked': False
            }
        )
        soup = BeautifulSoup(rendered, "lxml")
        self.assertIn('<p>Some field</p>', rendered)
        self.assertEqual(0, len(soup.find_all('a')))

    def test_renders_paragraph_if_form_locked(self):
        """
        The template should just render a paragraph
        """
        rendered = render_to_string(
            'modeladmin/omniforms/wagtail/includes/related_controls.html',
            {
                'button_text': 'Some field',
                'edit_url': '/dummy-path/edit/',
                'delete_url': '/dummy-path/delete/',
                'form_locked': True
            }
        )
        soup = BeautifulSoup(rendered, "lxml")
        self.assertIn('<p>Some field</p>', rendered)
        self.assertEqual(0, len(soup.find_all('a')))

    def test_renders_dropdown_with_edit_url(self):
        """
        The template should just render a dropdown with a link
        """
        rendered = render_to_string(
            'modeladmin/omniforms/wagtail/includes/related_controls.html',
            {
                'button_text': 'Some field',
                'edit_url': '/some/path/',
                'delete_url': None,
                'form_locked': False
            }
        )
        soup = BeautifulSoup(rendered, "lxml")
        dropdown_link = soup.find('a', {'class': 'c-dropdown__button'})
        edit_links = soup.find_all('a', {'class': 'u-link'})
        self.assertEqual(dropdown_link.text.strip(), 'Some field')
        self.assertEqual(1, len(edit_links))
        self.assertEqual(edit_links[0].attrs['href'].strip(), '/some/path/')
        self.assertEqual(edit_links[0].text.strip(), 'Edit')

    def test_renders_dropdown_with_delete_url(self):
        """
        The template should just render a dropdown with a link
        """
        rendered = render_to_string(
            'modeladmin/omniforms/wagtail/includes/related_controls.html',
            {
                'button_text': 'Some field',
                'edit_url': None,
                'delete_url': '/some/path/',
                'form_locked': False
            }
        )
        soup = BeautifulSoup(rendered, "lxml")
        dropdown_link = soup.find('a', {'class': 'c-dropdown__button'})
        delete_links = soup.find_all('a', {'class': 'u-link'})
        self.assertEqual(dropdown_link.text.strip(), 'Some field')
        self.assertEqual(1, len(delete_links))
        self.assertEqual(delete_links[0].attrs['href'].strip(), '/some/path/')
        self.assertEqual(delete_links[0].text.strip(), 'Delete')

    def test_renders_dropdown_with_edit_and_delete_url(self):
        """
        The template should just render a dropdown with 2 links
        """
        rendered = render_to_string(
            'modeladmin/omniforms/wagtail/includes/related_controls.html',
            {
                'button_text': 'Some field',
                'edit_url': '/some/path/edit/',
                'delete_url': '/some/path/delete/'
            }
        )
        soup = BeautifulSoup(rendered, "lxml")
        dropdown_link = soup.find('a', {'class': 'c-dropdown__button'})
        links = soup.find_all('a', {'class': 'u-link'})
        self.assertEqual(dropdown_link.text.strip(), 'Some field')
        self.assertEqual(2, len(links))
