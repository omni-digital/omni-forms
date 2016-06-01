# -*- coding: utf-8 -*-
"""
Django settings for omniforms app.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '%uf85o7ni^lao=5#e*dfdpvn3zze#g(gu257q9o6%+(-jheu1-'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
