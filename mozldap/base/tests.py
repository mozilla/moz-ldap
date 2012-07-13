# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import ldap
import mock
from nose.tools import eq_, ok_
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse


class ViewsTestCase(TestCase):

    def setUp(self):
        super(ViewsTestCase, self).setUp()
        ldap.open = mock.Mock('ldap.open')
        ldap.open.mock_returns = mock.Mock('ldap_connection')
        ldap.set_option = mock.Mock(return_value=None)
        assert 'LocMemCache' in settings.CACHES['default']['BACKEND']

    def tearDown(self):
        super(ViewsTestCase, self).tearDown()
        from django.core.cache import cache
        cache.clear()

    def test_render_home_page(self):
        url = reverse('home')
        response = self.client.get(url)
        eq_(response.status_code, 200)

    def test_exists(self):
        url = reverse('exists')
        response = self.client.get(url)
        eq_(response.status_code, 400)

        response = self.client.get(url, {'mail': ''})
        eq_(response.status_code, 400)

        XXXX
        response = self.client.get(url, {'mail': 'peter@example.com'})
        eq_(response.status_code, 200)
