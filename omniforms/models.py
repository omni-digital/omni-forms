# -*- coding: utf-8 -*-
"""
Models for the omniforms app
"""
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class OmniFormBase(models.Model):
    """
    Base class for the OmniForm model
    """
    title = models.CharField(max_length=255)

    class Meta(object):
        """
        Django properties
        """
        abstract = True

    def __str__(self):
        """
        Method for generating a string representation of the instance

        :return: String representation of the instance
        """
        return self.title


class OmniModelFormBase(OmniFormBase):
    """
    Base class for the OmniModelForm model
    """
    content_type = models.ForeignKey(ContentType, related_name='+')

    class Meta(object):
        """
        Django properties
        """
        abstract = True
