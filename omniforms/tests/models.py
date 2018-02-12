from django.db import models
from omniforms.models import OmniField


class DummyModel3(models.Model):
    """
    Dummy Model 2 for use with tests
    """
    title = models.ManyToManyField('tests.DummyModel')


class DummyModel2(models.Model):
    """
    Dummy Model 2 for use with tests
    """
    title = models.CharField(max_length=255)


class DummyModel(models.Model):
    """
    Dummy Model for use with tests
    """
    title = models.CharField(max_length=255)
    agree = models.BooleanField()
    some_date = models.DateField(blank=True, null=True)
    some_date_1 = models.DateField(auto_now=True)
    some_date_2 = models.DateField(auto_now_add=True)
    some_datetime = models.DateTimeField()
    some_datetime_1 = models.DateTimeField(auto_now=True)
    some_datetime_2 = models.DateTimeField(auto_now_add=True)
    some_decimal = models.DecimalField(decimal_places=10, max_digits=12)
    some_email = models.EmailField()
    some_float = models.FloatField()
    some_integer = models.IntegerField()
    some_time = models.TimeField()
    some_time_1 = models.TimeField(auto_now=True)
    some_time_2 = models.TimeField(auto_now_add=True)
    some_url = models.URLField()
    slug = models.SlugField()
    other_models = models.ManyToManyField(DummyModel2)


class TaggableManagerField(OmniField):
    """
    Model to test custom field mappings
    """
    initial_data = None


class TaggableManagerInvalidField(models.Model):
    """
    Model to test custom field mappings
    """
    initial_data = None
