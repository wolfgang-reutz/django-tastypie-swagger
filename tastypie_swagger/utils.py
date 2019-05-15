try:
    # python 3.x
    from urllib.parse import urljoin
except ModuleNotFoundError:
    # python 2.x
    from urlparse import urljoin

from django.conf import settings


def trailing_slash_or_none():
    """
    Return a slash or empty string based on tastypie setting
    """
    if getattr(settings, 'TASTYPIE_ALLOW_MISSING_SLASH', False):
        return ''
    return '/'


def urljoin_forced(base, path, **kwargs):
    """
    urljoin base with path, except append '/' to base if it doesnt exist
    """
    if not base:
        base = '/'
    base = base.endswith('/') and base or '%s/' % base
    return urljoin(base, path, **kwargs)
