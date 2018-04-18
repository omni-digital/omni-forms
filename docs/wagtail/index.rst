Wagtail integration
===================

Installation
------------

In addition to the steps outlined in the 'Getting started' section you will need to add the ``omniforms.wagtail`` app to your projects ``INSTALLED_APPS`` setting.

.. code-block:: python

    INSTALLED_APPS += ['omni_forms', 'omni_forms.wagtail']

Once you've done this you will need to run the database migrations that come bundled with the omniforms app.

.. code-block:: python

    python manage.py migrate

You should now be able to create and manage forms using the wagtail admin interface.

Custom admin forms
~~~~~~~~~~~~~~~~~~

TODO: POPULATE

Locking forms
~~~~~~~~~~~~~

TODO: POPULATE
