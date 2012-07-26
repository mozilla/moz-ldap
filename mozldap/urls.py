from django.conf.urls.defaults import patterns, include

from .base import urls

from funfactory.monkeypatches import patch
patch()


urlpatterns = patterns('',
    # Example:
    (r'', include(urls)),

)


handler404 = 'mozldap.base.views.handler404'
