Configuration
=============

The OmniForms application can be configured in a number of different ways:

OmniModelForm permitted content types
-------------------------------------

You may not want administrators to be able to create forms for all different types of content in your database.

There are 2 different ways of restricting the types of content that can be associated with model forms created through the admin interface:

OMNI_FORMS_CONTENT_TYPES
~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to define specific apps and/or models which can be used by the omniforms app using the ``OMNI_FORMS_CONTENT_TYPES`` setting.

The following configuration would allow _any_ of the models in the app ``foo``, and the ``modelone`` and ``modeltwo`` models within the ``bar`` app, to be used.

.. code-block:: python

    OMNI_FORMS_CONTENT_TYPES = [
        {'app_label': 'foo'},
        {'app_label': 'bar', 'model': 'modelone'},
        {'app_label': 'bar', 'model': 'modeltwo'},
    ]

If the ``OMNI_FORMS_CONTENT_TYPES`` setting is not defined it will default to None and the ``OMNI_FORMS_EXCLUDED_CONTENT_TYPES`` setting will be used instead.

OMNI_FORMS_EXCLUDED_CONTENT_TYPES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to prevent model forms from being created for specific apps or specific models using the ``OMNI_FORMS_EXCLUDED_CONTENT_TYPES`` setting.

The following configuration would prevent forms being created for *any* of the models in the app ``foo``, and for the ``modelone`` and ``modeltwo`` models within the ``bar`` app.

.. code-block:: python

    OMNI_FORMS_EXCLUDED_CONTENT_TYPES = [
        {'app_label': 'foo'},
        {'app_label': 'bar', 'model': 'modelone'},
        {'app_label': 'bar', 'model': 'modeltwo'},
    ]

This setting defaults to the following if not overridden:

.. code-block:: python

    OMNI_FORMS_EXCLUDED_CONTENT_TYPES = [
        {'app_label': 'omniforms'}
    ]

This will prevent administrators from creating forms for managing omniforms. It's worth mentioning that allowing administrators to do this represents a potential security risk and should be avoided. As such, if you need to define your own ``OMNI_FORMS_EXCLUDED_CONTENT_TYPES`` setting it would be wise to exclude all ``omniforms`` models as shown above.

OMNI_FORMS_CUSTOM_FIELD_MAPPING
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although the omniforms app accounts for the majority of use cases, you may have models that use custom model fields. Omniforms will not be able to map these model fields to their corresponding form fields. As such you will need to provide a custom field mapping dictionary using the ``OMNI_FORMS_CUSTOM_FIELD_MAPPING`` setting.

 - Each key within the mapping dictionary must be a string (python dotted import path) to a model field class.
 - Each value within the mapping dictionary must be a string (python dotted import path) to an OmniField subclass.

For example, you can map a TagField to an OmniCharField model instance using the following configuration:

.. code-block:: python

    OMNI_FORMS_CUSTOM_FIELD_MAPPING = {
        'taggit.TagField': 'omniforms.models.OmniCharField',
    }

With this configuration any instances of ``taggit.TagField`` on your models will be represented as ``django.forms.CharField`` instances in ``OmniModelForm`` instances created via the admin.

This mechanism also allows custom ``OmniField`` model classes to be defined and used on a per-model-field basis.

.. code-block:: python

    OMNI_FORMS_CUSTOM_FIELD_MAPPING = {
        'taggit.TagField': 'my_app.MySuperOmniField',
    }

It is important to note that the dictionary values defined within the ``OMNI_FORMS_CUSTOM_FIELD_MAPPING`` **MUST** be subclasses of ``omniforms.models.OmniField``. If you attempt to register fields that do not subclass ``omniforms.models.OmniField`` an ``ImproperlyConfigured`` exception will be raised by the application.
