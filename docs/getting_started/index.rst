Getting started
===============

Installation
------------

Omniforms is built on the `Django web framework <https://www.djangoproject.com/>`_. This document assumes that you already have this installed. If not, you will need to install it:

Once you have django installed, the quickest way to install OmniForms is:

.. code-block:: console

    $ pip install omniforms

(``sudo`` may be required if installing system-wide or without virtualenv)

Once Omniforms is installed into your python environment, you will need to add the omniforms library to the  ``INSTALLED_APPS`` in your django projects settings file.

.. code-block:: python

    INSTALLED_APPS += ['omniforms']

Once you've done this you will need to run the database migrations that come bundled with the omniforms app.

.. code-block:: python

    python manage.py migrate

You should now be able to create and manage forms using the django admin interface.
