Wagtail integration
===================

Installation
------------

In addition to the steps outlined in the 'Getting started' section you will need to add the ``omniforms.wagtail`` app to your projects ``INSTALLED_APPS`` setting.

.. code-block:: python

    INSTALLED_APPS += ['omniforms', 'omniforms.wagtail']

Once you've done this you will need to run the database migrations that come bundled with the omniforms app.

.. code-block:: python

    python manage.py migrate

You should now be able to create and manage forms using the wagtail admin interface.

Custom admin forms
------------------

In some cases it may be desirable to customize the form class that wagtail uses in the admin for managing a custom related model type (i.e. an ``OmniForm`` Field or ``OmniFormHandler`` model). If this is desirable, the custom form class needs to be assigned to a ``base_form_class`` property on the model. e.g.

.. code-block:: python

    class MyOmniFieldForm(forms.ModelForm):
        def clean_name(self, value):
            if value.contains("something"):
                raise ValidationError("The field name cannot contain the word 'something'")
            return value

    class MyOmniField(OmniField):
        base_form_class = MyOmniFieldForm

It is worth noting that the ``base_form_class`` *must* subclass ``django.forms.ModelForm``.  You do *not* need to specify the model that the form is for (using the forms meta class) as this will be generated dynamically when the form class is created.

Locking forms
-------------

It may be desirable for forms to be locked under certain conditions. For example, if a form has been set up for data collection, and has already collected data, you may want to prevent the form from being modified or deleted. For this purpose we have added a custom wagtail hook which can be used to implement logic to prevent the form from being edited further.

The hook name is ``omniform_permission_check`` and is registered like any other wagtail hook. The hook takes 3 positional arguments:

 - ``action``: The type of action being performed on the form (clone, update, delete);
 - ``instance``: The form instance
 - ``user``: The currently logged in user

Example
~~~~~~~

.. code-block:: python

    from wagtail.wagtailcore import hooks

    @hooks.register('omniform_permission_check')
    def lock_form(action, form, user):
        if action in ['update', 'delete'] and form.some_relationship.count() > 0:
            raise PermissionDenied
