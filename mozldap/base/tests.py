# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import mock
from nose.tools import eq_, ok_
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse


class ViewsTestCase(TestCase):

    def setUp(self):
        super(ViewsTestCase, self).setUp()

        self.ldap_patcher = mock.patch('ldap.initialize')
        self.initialize = self.ldap_patcher.start()
        self.connection = mock.MagicMock('connection')
        self.connection.set_option = mock.MagicMock()
        self.connection.simple_bind_s = mock.MagicMock()
        self.initialize.return_value = self.connection

        assert 'LocMemCache' in settings.CACHES['default']['BACKEND']

    def tearDown(self):
        super(ViewsTestCase, self).tearDown()
        from django.core.cache import cache
        cache.clear()

        self.ldap_patcher.stop()

    def test_render_home_page(self):
        url = reverse('home')
        response = self.client.get(url)
        eq_(response.status_code, 302)

    def test_exists(self):
        url = reverse('exists')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        response = self.client.get(url, {'mail': ''})
        eq_(response.status_code, 400)

        result = {
            'abc123': {'uid': 'abc123', 'mail': 'peter@example.com'},
        }

        def search_s(base, scope, filterstr, *args, **kwargs):
            if 'peter@example.com' in filterstr:
                if 'hgaccountenabled=true' in filterstr:
                    return []
                return result.items()
            return []

        self.connection.search_s = mock.MagicMock(side_effect=search_s)

        response = self.client.get(url, {'mail': 'peter@example.com'})
        eq_(response.status_code, 200)
        eq_('application/json; charset=UTF-8', response['Content-Type'])
        eq_(json.dumps(result['abc123']).strip(), response.content.strip())

        response = self.client.get(url, {'mail': 'never@heard.of.com'})
        eq_(response.status_code, 200)
        eq_(response.content, '{}')

        response = self.client.get(url, {'mail': 'peter@example.com',
                                         'hgaccountenabled': ''})
        eq_(response.status_code, 200)
        eq_(response.content, '{}')

        response = self.client.get(url, {'mail': 'peter@example.com',
                                         'gender': 'male'})
        eq_(response.status_code, 200)

    def test_employee(self):
        url = reverse('employee')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        response = self.client.get(url, {'mail': ''})
        eq_(response.status_code, 400)

        result = {
            'abc123': {'uid': 'abc123',
                       'mail': 'peter@mozilla.com',
                       'sn': u'B\xe3ngtsson'},
        }

        def search_s(base, scope, filterstr, *args, **kwargs):
            if 'peter@example.com' in filterstr:
                return result.items()
            return []

        self.connection.search_s = mock.MagicMock(side_effect=search_s)

        response = self.client.get(url, {'mail': 'peter@example.com'})
        eq_(response.status_code, 200)
        eq_('application/json; charset=UTF-8', response['Content-Type'])
        eq_(json.dumps(result['abc123']).strip(), response.content.strip())

        response = self.client.get(url, {'mail': 'never@heard.of.com'})
        eq_(response.status_code, 200)
        eq_('application/json; charset=UTF-8', response['Content-Type'])
        eq_(response.content, '{}')

    def test_in_group(self):
        url = reverse('in-group')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        response = self.client.get(url, {'mail': ''})
        eq_(response.status_code, 400)

        response = self.client.get(url, {'mail': 'peter@example.com'})
        eq_(response.status_code, 400)

        response = self.client.get(url, {'mail': 'peter@example.com',
                                         'cn': ''})
        eq_(response.status_code, 400)

        result = {
            'abc123': {'uid': 'abc123', 'mail': 'peter@example.com'},
        }

        def search_s(base, scope, filterstr, *args, **kwargs):
            if 'ou=groups' in base:
                if ('peter@example.com' in filterstr and
                    'cn=CrashStats' in filterstr):
                    return result.items()
            else:
                # basic lookup
                if 'peter@example.com' in filterstr:
                    return result.items()
            return []

        self.connection.search_s = mock.MagicMock(side_effect=search_s)

        response = self.client.get(url, {'mail': 'peter@example.com',
                                         'cn': 'CrashStats'})
        eq_(response.status_code, 200)

        response = self.client.get(url, {'mail': 'peter@example.com',
                                         'cn': 'NotInGroup'})
        eq_(response.status_code, 200)
        eq_(response.content, '{}')
