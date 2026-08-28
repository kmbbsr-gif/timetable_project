# ============================================================
# 1. Patch Django's Context.__copy__ for Python 3.14+
# ============================================================
import sys
import django.template.context
from django.template import Context

# Completely override __copy__ to avoid super() issues
def _patched_copy(self):
    new = Context(self.dicts)
    new.dicts = self.dicts[:]
    return new

Context.__copy__ = _patched_copy

# ============================================================
# 2. Celery app (optional)
# ============================================================
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    celery_app = None
    __all__ = ()