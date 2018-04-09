from django import forms
from django.test import TestCase

from omniforms.wagtail.templatetags import wagtail_omni_forms_tags


class FormTestCaseStub(TestCase):
    """
    Testing stub for testing form related functionality
    """
    class DummyForm(forms.Form):
        title = forms.CharField(
            widget=forms.TextInput,
            required=True
        )
        description = forms.CharField(
            widget=forms.Textarea,
            required=False
        )
        agree = forms.BooleanField(
            required=True
        )
        age = forms.IntegerField(
            required=True
        )
        some_date = forms.DateField(
            required=True
        )
        some_datetime = forms.DateTimeField(
            required=True
        )
        some_time = forms.TimeField(
            required=True
        )
        choices = forms.ChoiceField(
            required=False,
            choices=[
                [1, 'One'],
                [2, 'Two']
            ]
        )

    def setUp(self):
        super(FormTestCaseStub, self).setUp()
        self.form = self.DummyForm()


class AdminFieldClassesForFieldTestCase(FormTestCaseStub):
    """
    Tests the admin_field_classes_for_field template tag
    """
    def test_title_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['title']).split()
        self.assertEqual(2, len(classes))
        self.assertIn('field', classes)
        self.assertIn('char_field', classes)

    def test_description_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['description']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('char_field', classes)
        self.assertIn('admin_auto_height_text_input', classes)

    def test_agree_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['agree']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('boolean_field', classes)
        self.assertIn('checkbox_input', classes)

    def test_age_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['age']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('integer_field', classes)
        self.assertIn('number_input', classes)

    def test_choices_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['choices']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('typed_choice_field', classes)
        self.assertIn('select', classes)

    def test_some_date_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['some_date']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('date_field', classes)
        self.assertIn('admin_date_input', classes)

    def test_some_datetime_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['some_datetime']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('date_time_field', classes)
        self.assertIn('admin_date_time_input', classes)

    def test_some_time_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_field(self.form['some_time']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('field', classes)
        self.assertIn('time_field', classes)
        self.assertIn('admin_time_input', classes)


class AdminFieldClassesForObjectTestCase(FormTestCaseStub):
    """
    Tests the admin_field_classes_for_object template tag
    """
    def test_title_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['title']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('object', classes)
        self.assertIn('required', classes)
        self.assertIn('char_field', classes)

    def test_description_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['description']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('object', classes)
        self.assertIn('char_field', classes)
        self.assertIn('admin_auto_height_text_input', classes)

    def test_agree_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['agree']).split()
        self.assertEqual(4, len(classes))
        self.assertIn('object', classes)
        self.assertIn('required', classes)
        self.assertIn('boolean_field', classes)
        self.assertIn('checkbox_input', classes)

    def test_age_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['age']).split()
        self.assertEqual(4, len(classes))
        self.assertIn('object', classes)
        self.assertIn('required', classes)
        self.assertIn('integer_field', classes)
        self.assertIn('number_input', classes)

    def test_choices_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['choices']).split()
        self.assertEqual(3, len(classes))
        self.assertIn('object', classes)
        self.assertIn('typed_choice_field', classes)
        self.assertIn('select', classes)

    def test_some_date_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['some_date']).split()
        self.assertEqual(4, len(classes))
        self.assertIn('object', classes)
        self.assertIn('required', classes)
        self.assertIn('date_field', classes)
        self.assertIn('admin_date_input', classes)

    def test_some_datetime_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['some_datetime']).split()
        self.assertEqual(4, len(classes))
        self.assertIn('object', classes)
        self.assertIn('required', classes)
        self.assertIn('date_time_field', classes)
        self.assertIn('admin_date_time_input', classes)

    def test_some_time_classes(self):
        """
        The template tag should return the correct classes
        """
        classes = wagtail_omni_forms_tags.admin_field_classes_for_object(self.form['some_time']).split()
        self.assertEqual(4, len(classes))
        self.assertIn('object', classes)
        self.assertIn('required', classes)
        self.assertIn('time_field', classes)
        self.assertIn('admin_time_input', classes)

    def test_error_classes(self):
        """
        Ensures that the classes contains 'error'
        """
        def assert_contains_error(field):
            classes = wagtail_omni_forms_tags.admin_field_classes_for_object(field).split()
            self.assertIn('error', classes)

        def assert_not_contains_error(field):
            classes = wagtail_omni_forms_tags.admin_field_classes_for_object(field).split()
            self.assertNotIn('error', classes)

        form = self.DummyForm(data={})
        self.assertFalse(form.is_valid())
        assert_contains_error(form['title'])
        assert_contains_error(form['agree'])
        assert_contains_error(form['age'])
        assert_not_contains_error(form['description'])
        assert_not_contains_error(form['choices'])
