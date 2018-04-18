Welcome to omniforms's documentation!
=====================================

Omni forms is a simple form builder written in `Python <https://www.python.org/>`_ and built on the `Django web framework <https://www.djangoproject.com/>`_.

Omniforms ships with integrations for the `Django <https://www.djangoproject.com/>`_ and `WagtailCMS <https://wagtail.io/>`_ admin interfaces allowing you to easily create and manage user facing forms for your django website.

Project Aims
------------

The Omniforms application aims to provide functionality by which user facing forms can be built and maintained through administration interfaces provided by the Django and Wagtail projects.

The application aims to be user friendly, developer friendly, extensible and pragmatic. All forms generated using this application are subclasses of either ``django.forms.Form`` or ``django.forms.ModelForm`` meaning developers are ultimately working with a forms library that is both familiar and predictable.

Overview
--------

The Omniforms application ships with 2 concrete ``OmniForm`` model classes:

 - ``omniforms.models.OmniForm``
 - ``omniforms.models.OmniModelForm``

Each of these models contains a ``title`` field (used for administration) and references to zero of more ``OmniField`` and ``OmniFormHandler`` model instances. In addition to these fields the ``OmniModelForm`` model holds a reference to the ``ContentType`` that the form manages.

Each of the concrete ``OmniForm`` models provides a ``get_form_class`` instance method which will generate and return an appropriate form class. This form classes fields will be built from all of the associated ``OmniField`` instances.  In addition the form will be constructed in such a way that all associated ``OmniFormHandler`` instances will be run when the form instances ``handle`` method is called.

Usage
-----

Basic form example:
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from django import forms
   from omniforms.models import OmniForm

   # Get an OmniForm model instance
   omniform_instance = OmniForm.objects.get(pk=1)

   # Generate a django form class from the OmniForm instance
   form_class = omniform_instance.get_form_class()
   assert issubclass(form_class, forms.Form)

   # Work with the form class as per any other django form
   form = form_class(request.POST)
   if form.is_valid():
      # Call the forms 'handle' method (runs defined form handlers)
      form.handle()

Model form example:
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from django import forms
   from omniforms.models import OmniModelForm

   # Get an OmniModelForm model instance
   omniform_instance = OmniModelForm.objects.get(pk=1)

   # Generate a django form class from the OmniModelForm instance
   form_class = omniform_instance.get_form_class()
   assert issubclass(form_class, forms.ModelForm)

   # Work with the form class as per any other django form
   form = form_class(request.POST)
   if form.is_valid():
      # Call the forms 'handle' method (runs defined form handlers)
      form.handle()

The library does not intend to dictate how generated forms should be *used*. This is left as an exercise for developers.

Compatibility
-------------

Omniforms is compatible with:

  * Django 1.11
  * Wagtail 1.11, 1.12, 1.13

Below are some useful links to help you get started with Omniforms.

Index
-----


.. toctree::
   :maxdepth: 2
   :titlesonly:

   getting_started/index
   configuration/index
   extending/index
   wagtail/index
