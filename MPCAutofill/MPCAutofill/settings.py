"""
Django settings for MPCAutofill project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
import sys
from typing import Optional, Any, Iterable

import django_stubs_ext
import environ
import sentry_sdk
from dynaconf import Dynaconf, Validator
from sentry_sdk.integrations.django import DjangoIntegration

# Required for MyPy type checking
# https://stackoverflow.com/q/67965529
django_stubs_ext.monkeypatch()

# Project root, build paths like this: BASEDIR / "path/to"
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
TEMPLATES_DIR = BASE_DIR / "templates"
DEFAULT_CONFIG = CONFIG_DIR / "default.toml"
USER_CONFIG = CONFIG_DIR / "user.toml"
PATREON_CACHE = CONFIG_DIR / "patreon.json"

"""
* DynaConf Environment

Notes:
    Values are prioritized and overwritten in the following order, 
    from lowest priority to highest:
        * /config/default.toml (Sane defaults config file)
        * /config/user.toml (User defined configs, if it exists)
        * OS Environment variables (As defined in docker-compose.yml, for example)
"""
# Default values are defined in "/config/default.toml"
# Define overriding settings in "/config/user.toml"
ENV = Dynaconf(
    environments=False,
    load_dotenv=False,
    envar_prefix=False,
    ignore_unknown_envvars=True,
    merge_enabled=True,
    settings_files=[
        str(DEFAULT_CONFIG),
        str(USER_CONFIG)
    ]
)

# Core Django Configuration
DEBUG = ENV.DJANGO.DEBUG
SECRET_KEY = ENV.DJANGO.SECRET_KEY
SALT_KEY = ENV.DJANGO.SALT_KEY
ALLOWED_HOSTS = ENV.DJANGO.ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = ENV.DJANGO.CSRF_TRUSTED_ORIGINS
CORS_ALLOWED_ORIGINS = ENV.DJANGO.CORS_ALLOWED_ORIGINS
SESSION_COOKIE_SECURE = ENV.DJANGO.SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE = ENV.DJANGO.CSRF_COOKIE_SECURE
PREPEND_WWW = ENV.DJANGO.PREPEND_WWW

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = ENV.DJANGO.LANG_CODE
TIME_ZONE = ENV.DJANGO.TIME_ZONE
USE_I18N = ENV.DJANGO.USE_I18N
USE_L10N = ENV.DJANGO.USE_L10N
USE_TZ = ENV.DJANGO.USE_TZ

# Unique site information
SITE_NAME = ENV.SITE.NAME
DESCRIPTION = ENV.SITE.DESCRIPTION
GAME = ENV.SITE.GAME
DISCORD = ENV.SITE.DISCORD
REDDIT = ENV.SITE.REDDIT

# Cardpicker configuration
DEFAULT_CARDBACK_FOLDER_PATH = ENV.CARDPICKER.DEFAULT_CARDBACK_FOLDER_PATH
DEFAULT_CARDBACK_IMAGE_NAME = ENV.CARDPICKER.DEFAULT_CARDBACK_IMAGE_NAME

# Database configuration
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = dict(default=ENV.DATABASE)
DEFAULT_AUTO_FIELD = ENV.DATABASE.DEFAULT_AUTO_FIELD

# Elasticsearch DSL settings
ELASTICSEARCH_HOST = ENV.ELASTICSEARCH.HOST
ELASTICSEARCH_PORT = ENV.ELASTICSEARCH.PORT
ELASTICSEARCH_USER = ENV.ELASTICSEARCH.USER or None
ELASTICSEARCH_PASSWORD = ENV.ELASTICSEARCH.PASSWORD or None
ELASTICSEARCH_AUTH = {
    "http_auth": (ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD)
} if ELASTICSEARCH_USER and ELASTICSEARCH_PASSWORD else {}
ELASTICSEARCH_DSL = {
    "default": {
        "hosts": f"{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}",
        **ELASTICSEARCH_AUTH
    }
}
ELASTICSEARCH_DSL_AUTOSYNC = False

# Unfold admin panel settings
# https://unfoldadmin.com/docs/
UNFOLD = {
    "SITE_TITLE": ENV.UNFOLD.SITE_TITLE,
    "SITE_HEADER": ENV.UNFOLD.SITE_HEADER,
    "SHOW_VIEW_ON_SITE": False
}

# Email for logging
EMAIL_BACKEND = ENV.EMAIL.BACKEND
EMAIL_HOST = ENV.EMAIL.HOST
EMAIL_HOST_USER = ENV.EMAIL.HOST_USER
EMAIL_HOST_PASSWORD = ENV.EMAIL.HOST_PASSWORD
EMAIL_PORT = ENV.EMAIL.PORT
EMAIL_USE_TLS = ENV.EMAIL.USE_TLS
EMAIL_USE_SSL = ENV.EMAIL.USE_SSL
EMAIL_SSL_CERTFILE = ENV.EMAIL.SSL_CERTFILE or None
EMAIL_SSL_KEYFILE = ENV.EMAIL.SSL_KEYFILE or None
TARGET_EMAIL = ENV.EMAIL.PUBLIC_ADDRESS
SERVER_EMAIL = ENV.EMAIL.SERVER_ADDRESS
DEFAULT_FROM_EMAIL = ENV.EMAIL.NOREPLY_ADDRESS
EMAIL_SUBJECT_PREFIX = ENV.EMAIL.SUBJECT_PREFIX
EMAIL_USE_LOCALTIME = ENV.EMAIL.USE_LOCALTIME
EMAIL_FILE_PATH = ENV.EMAIL.FILE_PATH or None
EMAIL_TIMEOUT = ENV.EMAIL.TIMEOUT or None
ADMINS = ENV.EMAIL.ADMINS

# Analytics integrations (ADVANCED)
GTAG = ENV.ANALYTICS.GOOGLE_TAG

# Apps and middleware configuration
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.inlines",
    "unfold.contrib.forms",
    "cardpicker.apps.CardpickerConfig",
    "accounts",
    "django_q",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_elasticsearch_dsl",
    "corsheaders"
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "MPCAutofill.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "MPCAutofill.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Static files (CSS, JavaScript, Images) and storage
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = CONFIG_DIR / "static"
STATICFILES_DIRS = [
    BASE_DIR / "cardpicker/static"
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

# Sentry integration (ADVANCED)
if len(sys.argv) >= 2 and sys.argv[1] != "runserver" and DEBUG is False and ENV.SENTRY.ENABLED:
    sentry_sdk.init(
        dsn=ENV.SENTRY.DSN,
        integrations=[DjangoIntegration()],
        send_default_pii=ENV.SENTRY.SEND_DEFAULT_PII,
        traces_sample_rate=ENV.SENTRY.TRACES_SAMPLE_RATE,
        profiles_sample_rate=ENV.SENTRY.PROFILES_SAMPLE_RATE
    )

# django-q2
Q_CLUSTER = {
    "name": "DjangoORM",
    "workers": 8,
    "recycle": 500,
    "timeout": 60 * 60 * 12,  # 12 hours - extreme upper limit
    "retry": 60 * 60 * 12 + 1,  # must be longer than timeout
    "max_attempts": 1,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 500,
    "cpu_affinity": 1,
    "label": "Django Q2",
    "orm": "default"
}
