from django.db import models
from omniforms.models import OmniField


class DummyModel(models.Model):
    """
    Dummy Model for use with tests
    """
    title = models.CharField(max_length=255)
    agree = models.BooleanField()
    some_date = models.DateField(blank=True, null=True)
    some_datetime = models.DateTimeField()
    some_decimal = models.DecimalField(decimal_places=10, max_digits=12)
    some_email = models.EmailField()
    some_float = models.FloatField()
    some_integer = models.IntegerField()
    some_time = models.TimeField()
    some_url = models.URLField()


class TaggableManagerField(OmniField):
    """
    Model to test custom field mappings
    """
    initial = None


class TaggableManagerInvalidField(models.Model):
    """
    Model to test custom field mappings
    """
    initial = None
