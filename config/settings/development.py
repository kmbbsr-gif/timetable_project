from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Optional: if you want PostgreSQL in development
# import dj_database_url
# DATABASES['default'] = dj_database_url.config(default=os.environ.get('DATABASE_URL'))