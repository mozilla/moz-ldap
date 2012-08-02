# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import ldap
from ldap.filter import filter_format
from django import http
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import View
from .utils import json_view, required_parameters, class_decorator


#====================================================================


def home(request):
    return redirect(reverse('docs-home'))


def handler404(request):
    # instead of django.views.defaults.page_not_found
    return http.HttpResponseNotFound(request.path, mimetype='text/plain')


#====================================================================


class BaseView(View):

    # default attributes to return
    attributes = ['uid', 'cn', 'sn', 'mail', 'givenName']

    @property
    def connection(self):
        conn = ldap.initialize(settings.LDAP_SERVER_URI)
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        for opt, value in settings.LDAP_GLOBAL_OPTIONS.items():
            conn.set_option(opt, value)
        conn.simple_bind_s(
            settings.LDAP_BIND_DN,
            settings.LDAP_BIND_PASSWORD
        )
        return conn

    @staticmethod
    def make_search_filter(data, any_parameter=False):
        params = []
        for key, value in data.items():
            if not isinstance(value, (list, tuple)):
                value = [value]
            for v in value:
                if not v:
                    v = 'TRUE'
                params.append(filter_format('(%s=%s)', (key, v)))
        search_filter = ''.join(params)
        if len(params) > 1:
            if any_parameter:
                search_filter = '(|%s)' % search_filter
            else:
                search_filter = '(&%s)' % search_filter
        return search_filter

#====================================================================


@class_decorator(json_view)
@class_decorator(required_parameters('mail'))
class Exists(BaseView):
    def get(self, request, **search):
        search = search or dict(request.GET.items())
        mail = search.pop('mail')
        search_filter = self.make_search_filter(
            dict(mail=mail, emailAlias=mail),
            any_parameter=True
        )
        if search:
            other_filter = self.make_search_filter(search)
            search_filter = '(&%s%s)' % (search_filter, other_filter)

        rs = self.connection.search_s(
            "dc=mozilla",
            ldap.SCOPE_SUBTREE,
            search_filter,
            self.attributes
        )
        for uid, result in rs:
            return dict(result)

        return {}


@class_decorator(json_view)
@class_decorator(required_parameters('mail'))
class Employee(BaseView):

    def get(self, request, **search):
        search = search or dict(request.GET.items())
        mail = search.pop('mail')
        mail_filter = self.make_search_filter(
            dict(mail=mail, emailAlias=mail),
            any_parameter=True
        )
        other_filter = self.make_search_filter(
            dict(search, objectClass='mozComPerson')
        )
        search_filter = '(&%s%s)' % (mail_filter, other_filter)

        rs = self.connection.search_s(
            "dc=mozilla",
            ldap.SCOPE_SUBTREE,
            search_filter,
            self.attributes
        )
        for uid, result in rs:
            return dict(result)

        return {}


@class_decorator(json_view)
@class_decorator(required_parameters('mail', 'cn'))
class InGroup(BaseView):

    def get(self, request, **search):
        cn = request.GET.get('cn')
        mail = request.GET.get('mail')

        # first, figure out the uid
        mail_filter = self.make_search_filter(dict(mail=mail))
        alias_filter = self.make_search_filter(dict(emailAlias=mail))
        search_filter = '(|%s%s)' % (mail_filter, alias_filter)

        rs = self.connection.search_s(
            "dc=mozilla",
            ldap.SCOPE_SUBTREE,
            search_filter,
            ['uid']
        )
        uid = None
        for uid, result in rs:
            break

        if not uid:
            return {}

        search_filter1 = self.make_search_filter(dict(cn=cn))
        search_filter2 = self.make_search_filter({
            'memberUID': [uid, mail],  # should that me 'memberuid' ??
            'member': ['mail=%s,o=com,dc=mozilla' % mail,
                       'mail=%s,o=org,dc=mozilla' % mail,
                       'mail=%s,o=net,dc=mozillacom' % mail],
        }, any_parameter=True)
        search_filter = '(&%s%s)' % (search_filter1, search_filter2)

        rs = self.connection.search_s(
            "ou=groups,dc=mozilla",
            ldap.SCOPE_SUBTREE,
            search_filter,
            ['cn']
        )

        for __ in rs:
            return {'group': 'OK'}

        return {}
