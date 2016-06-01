from django.db import models


class DummyModel(models.Model):
    """
    Dummy Model for use with tests
    """
    title = models.CharField(max_length=255)
