from mock import Mock, patch

from django import forms
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.urlresolvers import reverse
from django.test import override_settings, TestCase
from wagtail.wagtailcore.models import Page

from omniforms.admin_forms import AddRelatedForm
from omniforms.models import OmniCharField, OmniField, OmniFormHandler, OmniFormEmailHandler
from omniforms.tests.factories import OmniFormFactory, OmniCharFieldFactory, OmniFormEmailHandlerFactory, UserFactory
from omniforms.wagtail import model_admin_views
from omniforms.wagtail.forms import WagtailOmniFormCloneForm
from omniforms.wagtail.model_admin_views import OmniFormBaseView, RelatedFormView
from omniforms.wagtail.wagtail_hooks import WagtailOmniFormModelAdmin


class ModelAdminTestCaseStub(TestCase):
    """
    Test case stub for the model admin views
    """
    @classmethod
    def setUpTestData(cls):
        super(ModelAdminTestCaseStub, cls).setUpTestData()
        # Create a model admin instance and a form to work with
        cls.model_admin = WagtailOmniFormModelAdmin()
        cls.form = OmniFormFactory.create()
        # Get groups and permissions used in tests
        cls.editor_group = Group.objects.get(name='Editors')
        cls.add_permission = Permission.objects.get(codename='add_omniform')
        cls.change_permission = Permission.objects.get(codename='change_omniform')
        # Field permissions
        cls.add_charfield_permission = Permission.objects.get(codename='add_omnicharfield')
        cls.change_charfield_permission = Permission.objects.get(codename='change_omnicharfield')
        cls.delete_charfield_permission = Permission.objects.get(codename='delete_omnicharfield')
        # Handler permissions
        cls.add_emailhandler_permission = Permission.objects.get(codename='add_omniformemailhandler')
        cls.change_emailhandler_permission = Permission.objects.get(codename='change_omniformemailhandler')
        cls.delete_emailhandler_permission = Permission.objects.get(codename='delete_omniformemailhandler')
        # Handler permissions
        cls.add_emailconfirmationhandler_permission = Permission.objects.get(
            codename='add_omniformemailconfirmationhandler'
        )
        cls.change_emailconfirmationhandler_permission = Permission.objects.get(
            codename='change_omniformemailconfirmationhandler'
        )
        cls.delete_emailconfirmationhandler_permission = Permission.objects.get(
            codename='delete_omniformemailconfirmationhandler'
        )
        # Create a user to work with
        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super(ModelAdminTestCaseStub, self).setUp()
        # Assign omni forms permissions to user
        self.user.user_permissions.add(self.add_permission)
        self.user.user_permissions.add(self.change_permission)
        # Assign omni fields permissions to user
        self.user.user_permissions.add(self.add_charfield_permission)
        self.user.user_permissions.add(self.change_charfield_permission)
        self.user.user_permissions.add(self.delete_charfield_permission)
        # Assign omni handlers permissions to user
        self.user.user_permissions.add(self.add_emailhandler_permission)
        self.user.user_permissions.add(self.change_emailhandler_permission)
        self.user.user_permissions.add(self.delete_emailhandler_permission)
        # Assign omni handlers permissions to user
        self.user.user_permissions.add(self.add_emailconfirmationhandler_permission)
        self.user.user_permissions.add(self.change_emailconfirmationhandler_permission)
        self.user.user_permissions.add(self.delete_emailconfirmationhandler_permission)
        # Assign editor group to user
        self.user.groups.add(self.editor_group)
        # Save the user
        self.user.save()
        # Log the user in
        self.client.force_login(self.user)


class OmniFormBaseViewTestCase(TestCase):
    """
    Tests the OmniFormBaseView class
    """
    def test_get_model_permission(self):
        """
        The method should return the correct permission string
        """
        perm = OmniFormBaseView._get_model_permission(OmniCharField, 'add')
        self.assertEqual(perm, 'omniforms.add_omnicharfield')


class SelectFieldViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the SelectFieldView
    """
    def setUp(self):
        """
        Generates the select field url for the form
        """
        super(SelectFieldViewTestCase, self).setUp()
        self.url = self.model_admin.url_helper.get_action_url(
            'select_field',
            self.form.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/select_related.html')
        self.assertIsInstance(response.context['view'], model_admin_views.SelectFieldView)
        self.assertIsInstance(response.context['form'], AddRelatedForm)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(response.context['view'].get_page_title(), 'Select field to add to form')

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @override_settings(WAGTAIL_OMNI_FORM_OMITTED_FIELDS=['OmniDurationField', 'OmniFileField'])
    def test_form_choices(self):
        """
        The view should render the form with the correct choices
        """
        response = self.client.get(self.url)
        choices = response.context['form'].fields['choices'].choices
        self.assertTrue(len(choices) > 0)

        for instance in ContentType.objects.order_by('model'):
            model_class = instance.model_class()

            if not model_class:
                continue

            if model_class.__name__ in getattr(settings, 'WAGTAIL_OMNI_FORM_OMITTED_FIELDS', []):
                self.assertNotIn([instance.pk, instance.name], choices)
            elif issubclass(model_class, OmniField) and model_class != OmniField:
                self.assertIn([instance.pk, instance.name], choices)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_correct_page(self):
        """
        The view should redirect to the correct page
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.SelectFieldView(model_admin=model_admin, instance_pk=str(self.form.pk))
        content_type = ContentType.objects.get_for_model(OmniCharField)
        response = self.client.post(self.url, {'choices': content_type.pk})
        self.assertRedirects(
            response,
            view.url_helper.get_action_url(
                'add_field',
                quote(self.form.pk),
                content_type.pk
            )
        )


class SelectHandlerViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the SelectHandlerView
    """
    def setUp(self):
        """
        Generates the select handler url for the form
        """
        super(SelectHandlerViewTestCase, self).setUp()
        self.url = self.model_admin.url_helper.get_action_url(
            'select_handler',
            self.form.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/select_related.html')
        self.assertIsInstance(response.context['view'], model_admin_views.SelectHandlerView)
        self.assertIsInstance(response.context['form'], AddRelatedForm)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(response.context['view'].get_page_title(), 'Select handler to add to form')

    @override_settings(WAGTAIL_OMNI_FORM_OMITTED_HANDLERS=['OmniFormSaveInstanceHandler'])
    def test_form_choices(self):
        """
        The view should render the form with the correct choices
        """
        response = self.client.get(self.url)
        choices = response.context['form'].fields['choices'].choices
        self.assertTrue(len(choices) > 0)

        for instance in ContentType.objects.order_by('model'):
            model_class = instance.model_class()

            if not model_class:
                continue

            if model_class.__name__ in getattr(settings, 'WAGTAIL_OMNI_FORM_OMITTED_HANDLERS', []):
                self.assertNotIn([instance.pk, instance.name], choices)
            elif model_class == OmniFormHandler:
                self.assertNotIn([instance.pk, instance.name], choices)
            elif issubclass(model_class, OmniFormHandler):
                self.assertIn([instance.pk, instance.name], choices)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_correct_page(self):
        """
        The view should redirect to the correct page
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.SelectHandlerView(model_admin=model_admin, instance_pk=str(self.form.pk))
        content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        response = self.client.post(self.url, {'choices': content_type.pk})
        self.assertRedirects(
            response,
            view.url_helper.get_action_url(
                'add_handler',
                quote(self.form.pk),
                content_type.pk
            )
        )


class RelatedFormViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the RelatedFormView class
    """
    def setUp(self):
        super(RelatedFormViewTestCase, self).setUp()
        self.view = RelatedFormView(self.model_admin, str(self.form.pk))

    def test_get_base_form_class_default(self):
        """
        The method should return a basic model form by default
        """
        self.view.related_object_model_class = OmniFormEmailHandler
        self.assertEqual(self.view._get_base_form_class(), forms.ModelForm)

    def test_get_base_form_class_override(self):
        """
        The method should return the custom model form
        """
        class SomeForm(forms.ModelForm):
            pass

        class SomeModel(object):
            base_form_class = SomeForm

        self.view.related_object_model_class = SomeModel
        self.assertEqual(self.view._get_base_form_class(), SomeForm)

    def test_get_base_form_class_raises_exception(self):
        """
        The method should raise an ImproperlyConfigured exception
        """
        class SomeForm(forms.Form):
            pass

        class SomeModel(object):
            base_form_class = SomeForm

        self.view.related_object_model_class = SomeModel
        self.assertRaises(ImproperlyConfigured, self.view._get_base_form_class)


class CloneFormViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the CloneForm view
    """
    def setUp(self):
        super(CloneFormViewTestCase, self).setUp()
        self.url = self.model_admin.url_helper.get_action_url('clone_form', self.form.pk)

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/clone_form.html')
        self.assertIsInstance(response.context['view'], model_admin_views.CloneFormView)
        self.assertIsInstance(response.context['form'], WagtailOmniFormCloneForm)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(response.context['view'].get_page_title(), 'Clone form')

    @patch('omniforms.wagtail.forms.WagtailOmniFormCloneForm.save')
    def test_calls_form_save(self, save):
        """
        The view should call the forms save method and redirect to the index view
        """
        save.return_value = self.form
        response = self.client.post(self.url, {'title': 'cloned form'})
        save.assert_called_with()
        self.assertRedirects(response, self.model_admin.url_helper.index_url)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.add_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_clone_obj')
    def test_user_can_clone_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)


class AddFieldViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the AddFieldView
    """
    def setUp(self):
        super(AddFieldViewTestCase, self).setUp()
        self.field_content_type = ContentType.objects.get_for_model(OmniCharField)
        self.url = self.model_admin.url_helper.get_action_url(
            'add_field',
            self.form.pk,
            self.field_content_type.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/related_form.html')
        self.assertIsInstance(response.context['view'], model_admin_views.AddFieldView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)
        self.assertEqual(response.context['form'].instance.form, self.form)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(
            response.context['view'].get_page_title(),
            'Add {0} to form'.format(self.field_content_type.name)
        )

    @patch('omniforms.wagtail.model_admin_views.AddFieldView._get_base_form_class')
    def test_uses_correct_form_class(self, get_base_form_class):
        """
        The view should use the correct base form class
        """
        class MyForm(forms.ModelForm):
            pass
        get_base_form_class.return_value = MyForm
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'], MyForm)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_form(self):
        """
        The form should be constructed correctly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        expected_fields = [
            {
                'name': 'name',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'label',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'help_text',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': False,
                'initial': None
            },
            {
                'name': 'required',
                'field': forms.BooleanField,
                'widget': forms.CheckboxInput,
                'required': False,
                'initial': False
            },
            {
                'name': 'widget_class',
                'field': forms.CharField,
                'widget': forms.Select,
                'required': True,
                'initial': None
            },
            {
                'name': 'order',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': True,
                'initial': 0
            },
            {
                'name': 'content_type',
                'field': forms.ModelChoiceField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'object_id',
                'field': forms.IntegerField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'initial_data',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': False,
                'initial': None
            },
            {
                'name': 'max_length',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': False,
                'initial': 255
            },
            {
                'name': 'min_length',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': False,
                'initial': 0
            }
        ]

        self.assertEqual(form._meta.model, OmniCharField)
        for field_dict in expected_fields:
            field = form.fields[field_dict['name']]
            self.assertIsInstance(field, field_dict['field'])
            self.assertIsInstance(field.widget, field_dict['widget'])
            self.assertEqual(field.required, field_dict['required'])
            self.assertEqual(field.initial, field_dict['initial'])

    def test_returns_400_response_for_invalid_content_type(self):
        """
        The view should return a 400 response for an invalid content type
        """
        field_content_type = ContentType.objects.get_for_model(Page)
        url = self.model_admin.url_helper.get_action_url(
            'add_field',
            self.form.pk,
            field_content_type.pk
        )
        response = self.client.get(url)
        self.assertEqual(400, response.status_code)

    def test_returns_400_response_for_base_omni_field(self):
        """
        The view should return a 400 response for an base omni field content type
        """
        field_content_type = ContentType.objects.get_for_model(OmniField)
        url = self.model_admin.url_helper.get_action_url(
            'add_field',
            self.form.pk,
            field_content_type.pk
        )
        response = self.client.get(url)
        self.assertEqual(400, response.status_code)

    @override_settings(WAGTAIL_OMNI_FORM_OMITTED_FIELDS=['OmniCharField'])
    def test_returns_400_response_for_omitted_omni_field(self):
        """
        The view should return a 400 response for an omni field that has been explicitly omitted in settings
        """
        field_content_type = ContentType.objects.get_for_model(OmniCharField)
        url = self.model_admin.url_helper.get_action_url(
            'add_field',
            self.form.pk,
            field_content_type.pk
        )
        response = self.client.get(url)
        self.assertEqual(400, response.status_code)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch(
        'omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj',
        Mock(return_value=True)
    )
    def test_user_can_edit_obj_false_without_perm(self):
        """
        The view should return a 403 response if the user cannot add the field
        """
        self.user.user_permissions.remove(self.add_charfield_permission)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_index_page(self):
        """
        The view should redirect to the index page by default
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.AddFieldView(
            model_admin=model_admin,
            instance_pk=str(self.form.pk),
            related_object_ctype_id=str(self.field_content_type.pk)
        )
        response = self.client.post(self.url, {
            'name': 'first_name',
            'label': 'First name',
            'widget_class': 'django.forms.widgets.TextInput',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk
        })
        self.assertRedirects(response, view.index_url)

    def test_redirects_to_select_field_page(self):
        """
        The view should redirect to the select_field page
        """
        model_admin = WagtailOmniFormModelAdmin()
        response = self.client.post(self.url, {
            'name': 'first_name',
            'label': 'First name',
            'widget_class': 'django.forms.widgets.TextInput',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk,
            'save_and_add_another': ''
        })
        self.assertRedirects(response, model_admin.url_helper.get_action_url(
            'select_field',
            self.form.pk
        ))


class AddHandlerViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the AddHandlerView
    """
    def setUp(self):
        super(AddHandlerViewTestCase, self).setUp()
        self.handler_content_type = ContentType.objects.get_for_model(OmniFormEmailHandler)
        self.url = self.model_admin.url_helper.get_action_url(
            'add_handler',
            self.form.pk,
            self.handler_content_type.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/related_form.html')
        self.assertIsInstance(response.context['view'], model_admin_views.AddHandlerView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)
        self.assertEqual(response.context['form'].instance.form, self.form)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(
            response.context['view'].get_page_title(),
            'Add {0} to form'.format(self.handler_content_type.name)
        )

    @patch('omniforms.wagtail.model_admin_views.AddHandlerView._get_base_form_class')
    def test_uses_correct_form_class(self, get_base_form_class):
        """
        The view should use the correct base form class
        """
        class MyForm(forms.ModelForm):
            pass
        get_base_form_class.return_value = MyForm
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'], MyForm)
        self.assertIsInstance(response.context['form'], forms.ModelForm)

    def test_form(self):
        """
        The form should be constructed correctly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        expected_fields = [
            {
                'name': 'name',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'order',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': True,
                'initial': 0
            },
            {
                'name': 'content_type',
                'field': forms.ModelChoiceField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'object_id',
                'field': forms.IntegerField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'subject',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': None
            },
            {
                'name': 'recipients',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': True,
                'initial': None
            },
            {
                'name': 'template',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': True,
                'initial': None
            },
        ]

        self.assertEqual(form._meta.model, OmniFormEmailHandler)
        for field_dict in expected_fields:
            field = form.fields[field_dict['name']]
            self.assertIsInstance(field, field_dict['field'])
            self.assertIsInstance(field.widget, field_dict['widget'])
            self.assertEqual(field.required, field_dict['required'])
            self.assertEqual(field.initial, field_dict['initial'])

    def test_returns_400_response_for_invalid_content_type(self):
        """
        The view should return a 400 response for an invalid content type
        """
        content_type = ContentType.objects.get_for_model(Page)
        url = self.model_admin.url_helper.get_action_url(
            'add_handler',
            self.form.pk,
            content_type.pk
        )
        response = self.client.get(url)
        self.assertEqual(400, response.status_code)

    def test_returns_400_response_for_base_handler(self):
        """
        The view should return a 400 response for a base handler content type
        """
        content_type = ContentType.objects.get_for_model(OmniFormHandler)
        url = self.model_admin.url_helper.get_action_url(
            'add_handler',
            self.form.pk,
            content_type.pk
        )
        response = self.client.get(url)
        self.assertEqual(400, response.status_code)

    @override_settings(WAGTAIL_OMNI_FORM_OMITTED_HANDLERS=['OmniFormEmailHandler'])
    def test_returns_400_response_for_omitted_omni_handler(self):
        """
        The view should return a 400 response for an omni field that has been explicitly omitted in settings
        """
        response = self.client.get(self.url)
        self.assertEqual(400, response.status_code)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch(
        'omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj',
        Mock(return_value=True)
    )
    def test_user_can_edit_obj_false_without_perm(self):
        """
        The view should return a 403 response if the user cannot add the handler
        """
        self.user.user_permissions.remove(self.add_emailhandler_permission)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_index_page(self):
        """
        The view should redirect to the index page by default
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.AddHandlerView(
            model_admin=model_admin,
            instance_pk=str(self.form.pk),
            related_object_ctype_id=str(self.handler_content_type.pk)
        )
        response = self.client.post(self.url, {
            'name': 'handler',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk,
            'subject': 'Email subject',
            'recipients': 'recipient@example.com',
            'template': 'This is the template'
        })
        self.assertRedirects(response, view.index_url)

    def test_redirects_to_select_handler_page(self):
        """
        The view should redirect to the select_field page
        """
        model_admin = WagtailOmniFormModelAdmin()
        response = self.client.post(self.url, {
            'name': 'handler',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk,
            'subject': 'Email subject',
            'recipients': 'recipient@example.com',
            'template': 'This is the template',
            'save_and_add_another': ''
        })
        self.assertRedirects(response, model_admin.url_helper.get_action_url(
            'select_handler',
            self.form.pk
        ))


class ChangeFieldViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the ChangeFieldView
    """
    def setUp(self):
        super(ChangeFieldViewTestCase, self).setUp()
        self.field = OmniCharFieldFactory.create(form=self.form)
        self.url = self.model_admin.url_helper.get_action_url(
            'change_field',
            self.form.pk,
            self.field.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/related_form.html')
        self.assertIsInstance(response.context['view'], model_admin_views.ChangeFieldView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)
        self.assertEqual(response.context['form'].instance, self.field)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(
            response.context['view'].get_page_title(),
            'Change {0} field'.format(self.field.label)
        )

    def test_form(self):
        """
        The form should be constructed correctly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        expected_fields = [
            {
                'name': 'name',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': self.field.name
            },
            {
                'name': 'label',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': self.field.label
            },
            {
                'name': 'help_text',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': False,
                'initial': self.field.help_text
            },
            {
                'name': 'required',
                'field': forms.BooleanField,
                'widget': forms.CheckboxInput,
                'required': False,
                'initial': self.field.required
            },
            {
                'name': 'widget_class',
                'field': forms.CharField,
                'widget': forms.Select,
                'required': True,
                'initial': self.field.widget_class
            },
            {
                'name': 'order',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': True,
                'initial': self.field.order
            },
            {
                'name': 'content_type',
                'field': forms.ModelChoiceField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': self.field.content_type_id
            },
            {
                'name': 'object_id',
                'field': forms.IntegerField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': self.field.object_id
            },
            {
                'name': 'initial_data',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': False,
                'initial': self.field.initial_data
            },
            {
                'name': 'max_length',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': False,
                'initial': self.field.max_length
            },
            {
                'name': 'min_length',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': False,
                'initial': self.field.min_length
            }
        ]

        self.assertEqual(form._meta.model, OmniCharField)
        for field_dict in expected_fields:
            field = form.fields[field_dict['name']]
            self.assertIsInstance(field, field_dict['field'])
            self.assertIsInstance(field.widget, field_dict['widget'])
            self.assertEqual(field.required, field_dict['required'])
            self.assertEqual(form.initial[field_dict['name']], field_dict['initial'])

    def test_raises_404_if_field_not_associated_with_field(self):
        """
        The view should return a 404 response if the specified field is not associated with the specified form
        """
        url = self.model_admin.url_helper.get_action_url(
            'change_field',
            9999,
            self.field.pk
        )
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch(
        'omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj',
        Mock(return_value=True)
    )
    def test_user_can_edit_obj_false_without_perm(self):
        """
        The view should return a 403 response if the user cannot change the field
        """
        self.user.user_permissions.remove(self.change_charfield_permission)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_index_page(self):
        """
        The view should redirect to the index page
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.ChangeFieldView(
            model_admin=model_admin,
            instance_pk=str(self.form.pk),
            related_object_id=str(self.field.pk)
        )
        response = self.client.post(self.url, {
            'name': 'first_name',
            'label': 'First name',
            'widget_class': 'django.forms.widgets.TextInput',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk
        })
        self.assertRedirects(response, view.index_url)

    def test_redirects_to_select_field_page(self):
        """
        The view should redirect to the select_field page
        """
        model_admin = WagtailOmniFormModelAdmin()
        response = self.client.post(self.url, {
            'name': 'first_name',
            'label': 'First name',
            'widget_class': 'django.forms.widgets.TextInput',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk,
            'save_and_add_another': ''
        })
        self.assertRedirects(response, model_admin.url_helper.get_action_url(
            'select_field',
            self.form.pk
        ))


class ChangeHandlerViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the ChangeHandlerView
    """
    def setUp(self):
        super(ChangeHandlerViewTestCase, self).setUp()
        self.handler = OmniFormEmailHandlerFactory.create(form=self.form)
        self.url = self.model_admin.url_helper.get_action_url(
            'change_handler',
            self.form.pk,
            self.handler.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/related_form.html')
        self.assertIsInstance(response.context['view'], model_admin_views.ChangeHandlerView)
        self.assertIsInstance(response.context['form'], forms.ModelForm)
        self.assertEqual(response.context['form'].instance, self.handler)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(
            response.context['view'].get_page_title(),
            'Change {0} handler'.format(self.handler.name)
        )

    def test_form(self):
        """
        The form should be constructed correctly
        """
        response = self.client.get(self.url)
        form = response.context['form']
        expected_fields = [
            {
                'name': 'name',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': self.handler.name
            },
            {
                'name': 'order',
                'field': forms.IntegerField,
                'widget': forms.NumberInput,
                'required': True,
                'initial': self.handler.order
            },
            {
                'name': 'content_type',
                'field': forms.ModelChoiceField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': self.handler.content_type_id
            },
            {
                'name': 'object_id',
                'field': forms.IntegerField,
                'widget': forms.HiddenInput,
                'required': True,
                'initial': self.handler.object_id
            },
            {
                'name': 'subject',
                'field': forms.CharField,
                'widget': forms.TextInput,
                'required': True,
                'initial': self.handler.subject
            },
            {
                'name': 'recipients',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': True,
                'initial': self.handler.recipients
            },
            {
                'name': 'template',
                'field': forms.CharField,
                'widget': forms.Textarea,
                'required': True,
                'initial': self.handler.template
            },
        ]

        self.assertEqual(form._meta.model, OmniFormEmailHandler)
        for field_dict in expected_fields:
            field = form.fields[field_dict['name']]
            self.assertIsInstance(field, field_dict['field'])
            self.assertIsInstance(field.widget, field_dict['widget'])
            self.assertEqual(field.required, field_dict['required'])
            self.assertEqual(form.initial[field_dict['name']], field_dict['initial'])

    def test_raises_404_if_field_not_associated_with_field(self):
        """
        The view should return a 404 response if the specified handler is not associated with the specified form
        """
        url = self.model_admin.url_helper.get_action_url(
            'change_handler',
            9999,
            self.handler.pk
        )
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch(
        'omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj',
        Mock(return_value=True)
    )
    def test_user_can_edit_obj_false_without_perm(self):
        """
        The view should return a 403 response if the user cannot change the handler
        """
        self.user.user_permissions.remove(self.change_emailhandler_permission)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_index_page(self):
        """
        The view should redirect to the index page
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.ChangeFieldView(
            model_admin=model_admin,
            instance_pk=str(self.form.pk),
            related_object_id=str(self.handler.pk)
        )
        response = self.client.post(self.url, {
            'name': 'handler',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk,
            'subject': 'Email subject',
            'recipients': 'recipient@example.com',
            'template': 'This is the template'
        })
        self.assertRedirects(response, view.index_url)

    def test_redirects_to_select_handler_page(self):
        """
        The view should redirect to the select_handler page
        """
        model_admin = WagtailOmniFormModelAdmin()
        response = self.client.post(self.url, {
            'name': 'handler',
            'order': 0,
            'content_type': ContentType.objects.get_for_model(self.form).pk,
            'object_id': self.form.pk,
            'subject': 'Email subject',
            'recipients': 'recipient@example.com',
            'template': 'This is the template',
            'save_and_add_another': ''
        })
        self.assertRedirects(response, model_admin.url_helper.get_action_url(
            'select_handler',
            self.form.pk
        ))


class DeleteFieldViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the DeleteFieldView
    """
    def setUp(self):
        super(DeleteFieldViewTestCase, self).setUp()
        self.field = OmniCharFieldFactory.create(form=self.form)
        self.url = self.model_admin.url_helper.get_action_url(
            'delete_field',
            self.form.pk,
            self.field.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/delete_related.html')
        self.assertIsInstance(response.context['view'], model_admin_views.DeleteFieldView)
        self.assertIsInstance(response.context['form'], forms.Form)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(response.context['object'], self.field)
        self.assertEqual(
            response.context['view'].get_page_title(),
            'Delete {0} field'.format(self.field.label)
        )

    def test_raises_404_if_field_not_associated_with_field(self):
        """
        The view should return a 404 response if the specified field is not associated with the specified form
        """
        url = self.model_admin.url_helper.get_action_url(
            'change_field',
            9999,
            self.field.pk
        )
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch(
        'omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj',
        Mock(return_value=True)
    )
    def test_user_can_edit_obj_false_without_perm(self):
        """
        The view should return a 403 response if the user cannot delete the field
        """
        self.user.user_permissions.remove(self.delete_charfield_permission)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_correct_page(self):
        """
        The view should redirect to the correct page
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.DeleteFieldView(
            model_admin=model_admin,
            instance_pk=str(self.form.pk),
            related_object_id=str(self.field.pk)
        )
        response = self.client.post(self.url)
        self.assertRedirects(response, view.index_url)


class DeleteHandlerViewTestCase(ModelAdminTestCaseStub):
    """
    Tests the DeleteHandlerView
    """
    def setUp(self):
        super(DeleteHandlerViewTestCase, self).setUp()
        self.handler = OmniFormEmailHandlerFactory.create(form=self.form)
        self.url = self.model_admin.url_helper.get_action_url(
            'delete_handler',
            self.form.pk,
            self.handler.pk
        )

    def test_renders(self):
        """
        The view should render
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'modeladmin/omniforms/wagtail/delete_related.html')
        self.assertIsInstance(response.context['view'], model_admin_views.DeleteHandlerView)
        self.assertIsInstance(response.context['form'], forms.Form)
        self.assertIsInstance(response.context['model_admin'], WagtailOmniFormModelAdmin)
        self.assertEqual(response.context['instance'], self.form)
        self.assertEqual(response.context['object'], self.handler)
        self.assertEqual(
            response.context['view'].get_page_title(),
            'Delete {0} handler'.format(self.handler.name)
        )

    def test_raises_404_if_field_not_associated_with_field(self):
        """
        The view should return a 404 response if the specified handler is not associated with the specified form
        """
        url = self.model_admin.url_helper.get_action_url(
            'change_handler',
            9999,
            self.handler.pk
        )
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_login_required(self):
        """
        The view should only be accessible to logged in users
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('wagtailadmin_login'),
            self.url
        ))

    def test_permission_required(self):
        """
        The view should only be accessible to users with the correct permission
        """
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('omniforms.wagtail.utils.hooks.get_hooks')
    def test_permission_required_permission_hooks(self, get_hooks):
        """
        The view should not be accessible if one of the omniform_permission_check hooks raises PermissionError
        """
        def dummy_hook(*args):
            raise PermissionDenied
        get_hooks.return_value = [dummy_hook]
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch(
        'omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj',
        Mock(return_value=True)
    )
    def test_user_can_edit_obj_false_without_perm(self):
        """
        The view should return a 403 response if the user cannot delete the handler
        """
        self.user.user_permissions.remove(self.delete_emailhandler_permission)
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    @patch('django.contrib.auth.models.User.has_perm', Mock(return_value=True))
    @patch('omniforms.wagtail.wagtail_hooks.WagtailOmniFormPermissionHelper.user_can_edit_obj')
    def test_user_can_edit_obj_false(self, user_can_edit_obj):
        """
        The view should return a 403 response if the user cannot edit the form
        """
        user_can_edit_obj.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_redirects_to_correct_page(self):
        """
        The view should redirect to the correct page
        """
        model_admin = WagtailOmniFormModelAdmin()
        view = model_admin_views.DeleteFieldView(
            model_admin=model_admin,
            instance_pk=str(self.form.pk),
            related_object_id=str(self.handler.pk)
        )
        response = self.client.post(self.url)
        self.assertRedirects(response, view.index_url)
