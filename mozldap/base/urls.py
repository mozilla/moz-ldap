# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from django.conf.urls.defaults import patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^exists/?$', views.exists, name='exists'),
    url(r'^employee/?$', views.employee, name='employee'),
    url(r'^in-group/?$', views.in_group, name='in-group'),
)
