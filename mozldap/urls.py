from django.conf.urls import patterns, include

from .base import urls as base_urls
from .docs import urls as docs_urls

from funfactory.monkeypatches import patch
patch()


urlpatterns = patterns('',
    # Example:
    (r'', include(base_urls)),
    (r'docs', include(docs_urls)),

)


handler404 = 'mozldap.base.views.handler404'
