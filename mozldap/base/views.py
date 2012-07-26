# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import functools
import ldap
from ldap.filter import filter_format
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
            return http.HttpResponse(
                _json_clean(json.dumps(response)),
                content_type='application/json; charset=UTF-8'
            )
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


def handler404(request):
    # instead of django.views.defaults.page_not_found
    return http.HttpResponseNotFound(request.path, mimetype='text/plain')


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
    search_filter = _make_search_filter(request.GET)

    rs = connection.search_s(
        "dc=mozilla",
        ldap.SCOPE_SUBTREE,
        search_filter,
        attrs
    )
    for uid, result in rs:
        return dict(result)

    return http.HttpResponse('', status=204)


def _make_search_filter(data, any_parameter=False):
    params = []
    for key, value in data.items():
        if not isinstance(value, (list, tuple)):
            value = [value]
        for v in value:
            if not v:
                v = 'true'
            params.append(filter_format('(%s=%s)', (key, v)))
    search_filter = ''.join(params)
    if len(params) > 1:
        if any_parameter:
            search_filter = '(|%s)' % search_filter
        else:
            search_filter = '(&%s)' % search_filter
    return search_filter


@json_view
def employee(request):
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
    request_data = dict(request.GET.items())
    search_filter = _make_search_filter(dict(request_data,
                                             objectClass='mozComPerson'))
    rs = connection.search_s(
        "dc=mozilla",
        ldap.SCOPE_SUBTREE,
        search_filter,
        attrs
    )
    for uid, result in rs:
        return dict(result)

    return http.HttpResponse('', status=204)


def in_group(request):
    cn = request.GET.get('cn')
    if not cn:
        return http.HttpResponseBadRequest("Missing group name variable 'cn'")
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

    # first, figure out the uid
    search_filter = _make_search_filter(dict(mail=mail))
    rs = connection.search_s(
        "dc=mozilla",
        ldap.SCOPE_SUBTREE,
        search_filter,
        ['uid']
    )
    uid = None
    for uid, result in rs:
        break

    if not uid:
        return http.HttpResponse('', status=204)

    search_filter1 = _make_search_filter(dict(cn=cn))
    # : (|(memberuid=$uid)(memberuid=$mail)(member=mail=$mail,o=com,dc=mozilla)(member=mail=$mail,o=org,dc=mozilla)\
    #     (member=mail=$mail,o=net,dc=mozillacom))
    search_filter2 = _make_search_filter({
        'memberUid': [uid, mail],  # should that me 'memberuid' ??
        'member': ['mail=%s,o=com,dc=mozilla' % mail,
                   'mail=%s,o=org,dc=mozilla' % mail,
                   'mail=%s,o=net,dc=mozillacom' % mail],
    }, any_parameter=True)
    search_filter = '(&(%s)(%s))' % (search_filter1, search_filter2)

    rs = connection.search_s(
        "ou=groups,dc=mozilla",
        ldap.SCOPE_SUBTREE,
        search_filter,
        #attrs
    )

    for uid, result in rs:
        #print result
        return http.HttpResponse('OK\n', mimetype='text/plain')

    return http.HttpResponse('', status=204)
