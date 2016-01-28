# This file is just Python, with a touch of Django which means
# you can inherit and tweak settings to your hearts content.

# For Docker, the following environment variables are supported:
#  SENTRY_POSTGRES_HOST
#  SENTRY_POSTGRES_PORT
#  SENTRY_DB_NAME
#  SENTRY_DB_USER
#  SENTRY_DB_PASSWORD
#  SENTRY_REDIS_HOST
#  SENTRY_REDIS_PORT
#  SENTRY_REDIS_DB
#  SENTRY_MEMCACHED_HOST
#  SENTRY_MEMCACHED_PORT
#  SENTRY_FILESTORE_DIR
#  SENTRY_SERVER_EMAIL
#  SENTRY_EMAIL_HOST
#  SENTRY_EMAIL_PORT
#  SENTRY_EMAIL_USER
#  SENTRY_EMAIL_PASSWORD
#  SENTRY_EMAIL_USE_TLS
#  SENTRY_MAILGUN_API_KEY
#  SENTRY_SECRET_KEY
from sentry.conf.server import *  # NOQA

import os
import os.path
import requests

CONF_ROOT = os.path.dirname(__file__)

postgres = os.environ.get('SENTRY_POSTGRES_HOST') or (os.environ.get('POSTGRES_PORT_5432_TCP_ADDR') and 'postgres')
if postgres:
    DATABASES = {
        'default': {
            'ENGINE': 'sentry.db.postgres',
            'NAME': (
                os.environ.get('SENTRY_DB_NAME')
                or os.environ.get('POSTGRES_ENV_POSTGRES_USER')
                or 'postgres'
            ),
            'USER': (
                os.environ.get('SENTRY_DB_USER')
                or os.environ.get('POSTGRES_ENV_POSTGRES_USER')
                or 'postgres'
            ),
            'PASSWORD': (
                os.environ.get('SENTRY_DB_PASSWORD')
                or os.environ.get('POSTGRES_ENV_POSTGRES_PASSWORD')
                or ''
            ),
            'HOST': postgres,
            'PORT': (
                os.environ.get('SENTRY_POSTGRES_PORT')
                or ''
            ),
            'OPTIONS': {
                'autocommit': True,
            },
        },
    }

# You should not change this setting after your database has been created
# unless you have altered all schemas first
SENTRY_USE_BIG_INTS = True

# If you're expecting any kind of real traffic on Sentry, we highly recommend
# configuring the CACHES and Redis settings

###########
# General #
###########

# Instruct Sentry that this install intends to be run by a single organization
# and thus various UI optimizations should be enabled.
SENTRY_SINGLE_ORGANIZATION = True

#########
# Redis #
#########

# Generic Redis configuration used as defaults for various things including:
# Buffers, Quotas, TSDB

redis = os.environ.get('SENTRY_REDIS_HOST') or (os.environ.get('REDIS_PORT_6379_TCP_ADDR') and 'redis')
if not redis:
    raise Exception('Error: REDIS_PORT_6379_TCP_ADDR (or SENTRY_REDIS_HOST) is undefined, did you forget to `--link` a redis container?')

redis_port = os.environ.get('SENTRY_REDIS_PORT') or '6379'
redis_db = os.environ.get('SENTRY_REDIS_DB') or '0'

SENTRY_REDIS_OPTIONS = {
    'hosts': {
        0: {
            'host': redis,
            'port': redis_port,
            'db': redis_db,
        },
    },
}

#########
# Cache #
#########

# Sentry currently utilizes two separate mechanisms. While CACHES is not a
# requirement, it will optimize several high throughput patterns.

memcached = os.environ.get('SENTRY_MEMCACHED_HOST') or (os.environ.get('MEMCACHED_PORT_11211_TCP_ADDR') and 'memcached')
if memcached:
    memcached_port = (
        os.environ.get('SENTRY_MEMCACHED_PORT')
        or '11211'
    )
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': [memcached + ':' + memcached_port],
            'TIMEOUT': 3600,
        }
    }

# A primary cache is required for things such as processing events
SENTRY_CACHE = 'sentry.cache.redis.RedisCache'
SENTRY_CACHE_OPTIONS = SENTRY_REDIS_OPTIONS

#########
# Queue #
#########

# See https://docs.getsentry.com/on-premise/server/queue/ for more
# information on configuring your queue broker and workers. Sentry relies
# on a Python framework called Celery to manage queues.

CELERY_ALWAYS_EAGER = False
BROKER_URL = 'redis://' + redis + ':' + redis_port + '/' + redis_db

###############
# Rate Limits #
###############

# Rate limits apply to notification handlers and are enforced per-project
# automatically.

SENTRY_RATELIMITER = 'sentry.ratelimits.redis.RedisRateLimiter'

##################
# Update Buffers #
##################

# Buffers (combined with queueing) act as an intermediate layer between the
# database and the storage API. They will greatly improve efficiency on large
# numbers of the same events being sent to the API in a short amount of time.
# (read: if you send any kind of real data to Sentry, you should enable buffers)

SENTRY_BUFFER = 'sentry.buffer.redis.RedisBuffer'

##########
# Quotas #
##########

# Quotas allow you to rate limit individual projects or the Sentry install as
# a whole.

SENTRY_QUOTAS = 'sentry.quotas.redis.RedisQuota'

########
# TSDB #
########

# The TSDB is used for building charts as well as making things like per-rate
# alerts possible.

SENTRY_TSDB = 'sentry.tsdb.redis.RedisTSDB'

###########
# Digests #
###########

# The digest backend powers notification summaries.

SENTRY_DIGESTS = 'sentry.digests.backends.redis.RedisBackend'

################
# File storage #
################

# Any Django storage backend is compatible with Sentry. For more solutions see
# the django-storages package: https://django-storages.readthedocs.org/en/latest/

if 'SENTRY_FILES_BUCKET' in os.environ:
    SENTRY_FILESTORE = 'storages.backends.s3boto.S3BotoStorage'
    AWS_STORAGE_BUCKET_NAME = os.environ['SENTRY_FILES_BUCKET']
else:
    SENTRY_FILESTORE = 'django.core.files.storage.FileSystemStorage'
    SENTRY_FILESTORE_OPTIONS = {
        'location': os.environ['SENTRY_FILESTORE_DIR'],
    }

##############
# Web Server #
##############

# If you're using a reverse SSL proxy, you should enable the X-Forwarded-Proto
# header and uncomment the following settings

if 'SENTRY_USE_SSL' in os.environ:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True

SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = 9000
SENTRY_WEB_OPTIONS = {
    # 'workers': 3,  # the number of gunicorn workers
    # 'secure_scheme_headers': {'X-FORWARDED-PROTO': 'https'},
}

allow_host = os.environ.get('SENTRY_ALLOW_HOST')
if allow_host:
    ALLOWED_HOSTS = [allow_host]

if 'SENTRY_ALLOW_DETECTED_EC2_HOST' in os.environ:
    ec2_ip = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4', timeout=0.1).text
    ec2_hostname = requests.get('http://169.254.169.254/latest/meta-data/public-hostname', timeout=0.1).text
    try:
        ALLOWED_HOSTS.extend([ec2_ip, ec2_hostname])
    except NameError:
        ALLOWED_HOSTS = [ec2_ip, ec2_hostname]

###############
# Mail Server #
###############

# For more information check Django's documentation:
# https://docs.djangoproject.com/en/1.6/topics/email/

email = os.environ.get('SENTRY_EMAIL_HOST') or (os.environ.get('SMTP_PORT_25_TCP_ADDR') and 'smtp')
if email:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = email
    EMAIL_HOST_PASSWORD = os.environ.get('SENTRY_EMAIL_PASSWORD') or ''
    EMAIL_HOST_USER = os.environ.get('SENTRY_EMAIL_USER') or ''
    EMAIL_PORT = int(os.environ.get('SENTRY_EMAIL_PORT') or 25)
    EMAIL_USE_TLS = 'SENTRY_EMAIL_USE_TLS' in os.environ
elif 'SENTRY_SES_ENDPOINT' in os.environ:
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_REGION_ENDPOINT = os.environ['SENTRY_SES_ENDPOINT']
else:
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# The email address to send on behalf of
SERVER_EMAIL = os.environ.get('SENTRY_SERVER_EMAIL') or 'root@localhost'

# If you're using mailgun for inbound mail, set your API key and configure a
# route to forward to /api/hooks/mailgun/inbound/
MAILGUN_API_KEY = os.environ.get('SENTRY_MAILGUN_API_KEY') or ''

secret_key = os.environ.get('SENTRY_SECRET_KEY')
if secret_key:
    SECRET_KEY = secret_key

#########
# OAuth #
#########

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
