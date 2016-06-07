# Omni Forms

Omni forms is a simple form builder with admin integration for django versions >= 1.8.

## Installation

!Pypi release coming soon

Once the package has been installed just add `omni_forms` to `INSTALLED_APPS` in your settings file:

`INSTALLED_APPS += ('omni_forms',)`

Once you've done this run `python manage.py migrate` to migrate your database.

## Configuration

The OmniForms application can be configured in a number of different ways:

### Permitted content types

You may not want administrators to be able to create forms for _all_ different types of content in your database.
It is possible to prevent model forms from being created for specific apps or specific models using the `OMNI_FORMS_EXCLUDED_CONTENT_TYPES` setting.

For example:

The following configuration would prevent forms being created for _any_ of the models in the app `foo` and for the `modelone` and `modeltwo` models within the `bar` app.

```
OMNI_FORMS_EXCLUDED_CONTENT_TYPES = [
    {'app_label': 'foo'},
    {'app_label': 'bar', 'model': 'modelone'},
    {'app_label': 'bar', 'model': 'modeltwo'},
]
```

If you do not specify this setting it will default to the following:

```
OMNI_FORMS_EXCLUDED_CONTENT_TYPES = [
    {'app_label': 'omniforms'}
]
```

This will prevent administrators from creating form_builder forms with the formbuilder itself.
It's worth mentioning that allowing administrators to do this represents a potential security risk and should be avoided.
As such, if you need to define your own `OMNI_FORMS_EXCLUDED_CONTENT_TYPES` setting it would be wise to exclude all `omniforms` models as shown above.

## Compatibility

This app is compatible with the following django versions:

 - Django 1.8.x
 - Django 1.9.x

## ChangeLog

 - 0.1 - Initial Build
