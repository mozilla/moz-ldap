# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import functools
import ldap
from django import http
from django.shortcuts import render
from django.conf import settings


def json_view(f):
    @functools.wraps(f)
    def wrapper(*args, **kw):
        response = f(*args, **kw)
        if isinstance(response, http.HttpResponse):
            return response
        else:
            return http.HttpResponse(_json_clean(json.dumps(response)),
                                content_type='application/json; charset=UTF-8')
    return wrapper

def _json_clean(value):
    """JSON-encodes the given Python object."""
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    return value.replace("</", "<\\/")


def home(request):
    return http.HttpResponse('Yada yada yada\nDocumentation...')


@json_view
def exists(request):
    mail = request.GET.get('mail')
    if not mail:
        return http.HttpResponseBadRequest("Missing 'mail'")

    # XXX needs to be refactored out
    connection = ldap.initialize(settings.LDAP_SERVER_URI)
    connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
    for opt, value in settings.LDAP_GLOBAL_OPTIONS.items():
        connection.set_option(opt, value)
    connection.simple_bind_s(settings.LDAP_BIND_DN,
                             settings.LDAP_BIND_PASSWORD)

    attrs = ['uid', 'cn', 'sn', 'mail', 'givenName']
    search_filter = '(mail=%s)' % mail
    rs = connection.search_s(
      "dc=mozilla",
      ldap.SCOPE_SUBTREE,
      search_filter,
      attrs
    )
    for uid, result in rs:
        return dict(result)

    raise http.Http404('Not found')


def in_group(request):
    cn = request.GET.get('cn')
    if not cn:
        return http.HttpResponseBadRequest("Missing 'mail'")


    # XXX needs to be refactored out
    connection = ldap.initialize(settings.LDAP_SERVER_URI)
    connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
    for opt, value in settings.LDAP_GLOBAL_OPTIONS.items():
        connection.set_option(opt, value)
    connection.simple_bind_s(settings.LDAP_BIND_DN,
                             settings.LDAP_BIND_PASSWORD)

    attrs = ['uid', 'cn', 'sn', 'mail', 'givenName']
    search_filter = '(cn=%s)' % mail
    rs = connection.search_s(
      "dc=mozilla",
      ldap.SCOPE_SUBTREE,
      search_filter,
      attrs
    )
