Extending
=========

It is possible to add custom Field and Handler models to your application, therefore allowing you to extend the basic functionality provided by the ``OmniForms`` library. Once you have done so, the omniforms library should automatically find these models and make it possible to create and associate these fields and handlers with your OmniForm model instances.

Fields
------

It is possible to add custom field types to your application that can be used by the omniforms library.  Doing so should be as simple as adding a model class that subclasses ``omniforms.models.OmniField`` and provides a few class attributes used by the omniforms library.

At the very minimum, a custom Field model might look something like this:

.. code-block:: python

   from omniforms.models import OmniField

   class MyCustomOmniField(OmniField):
       """
       Custom OmniField model
       """
       FIELD_CLASS = 'django.forms.CharField'
       FORM_WIDGETS = (
           'django.forms.widgets.TextInput',
           'django.forms.widgets.Textarea',
           'django.forms.widgets.PasswordInput',
           'myapp.widgets.MyCustomFormWidget',
       )

Of course, it is also possible to implement more complex ``OmniField`` models. If you are interested in doing so it may be wise to look at ``omniforms.models.OmniChoiceField`` and ``omniforms.models.OmniMultipleChoiceField``.

The ``FIELD_CLASS`` attribute must be a python dotted import path to the form field class that this OmniField *will* use in the generated form. An OmniField modelo may only have one ``FIELD_CLASS`` (i.e. you cannot assign it a list or tuple of field classes) for the user to pick from.

The ``FORM_WIDGETS`` attribute must be a list or tuple containing a series of python dotted import paths to potential form widget classes that this OmniField *could* use in generated forms. This list or tuple must contain at least one potential widget but could have many. If there is more than one widget listed for a given OmniField model, the administrator should be able to select the type of widget they would like to use for a given field at the point of creation within the admin environment.  If only one type of widget is provided, this option is effectively removed from the form and pre-selected for the admin user.

Handlers
--------

It is possible to add custom form handler types to your application that can be used by the omniforms library.  Doing so should be as simple as adding a model class that subclasses ``omniforms.models.OmniFormHandler`` and implements a ``handle`` method.

The handle method should accept one positional argument, form, which will be the valid form instance.

At the very minimum, a custom Handler model might look something like this:

.. code-block:: python

   from omniforms.models import OmniFormHandler

   class MyCustomOmniFormHandler(OmniFormHandler):
       """
       Custom OmniFormHandler model
       """
       def handle(self, form):
           """
           Method for handling the valid form action

           :param form: The validated form instance this handler is attached to
           """
           do_something_with(form.cleaned_data)

It is worth noting that you should never call the forms ``handle`` or ``save`` (for model forms) methods within the ``OmniFormHandler.handle`` method. Doing so will cause the forms handlers to be run repeatedly until python reaches its recursion limit.

Omniforms ships with a handler - ``OmniFormSaveInstanceHandler`` - (to only be used with ``OmniModelForm`` instances) for saving model instances. This handler does not call the forms ``save`` method directly.  Instead it calls the ``django.forms.models.save_instance`` function which ensures that the form data is persisted to the database correctly, but avoids the issue of the forms handlers being run repeatedly.

This approach allows us to set up a series of form handlers that will run one after the other when the forms ``handle`` or ``save`` method is called.  For example, it is theoretically possible to implement and configure handlers to do the following:

 - Create a NewsLetterSubscription (model instance);
 - Send an email to the marketing department containing the subscribers data;
 - Post the users data to a CRM application;
 - Send an email to the subscriber confirming their subscription;
