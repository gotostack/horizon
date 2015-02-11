# Copyright 2015 Letv Cloud Computing
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers

INDEX_URL = reverse('horizon:azure:disks:index')


class DisksViewTests(helpers.TestCase):
    @helpers.create_stubs({
        api.azure_api: ('disk_list',)})
    def test_index(self):
        api_disks = self.azure_data_disks.list()

        api.azure_api.disk_list(
            IsA(http.HttpRequest)).AndReturn(api_disks)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'azure/disks/index.html')

        self.assertIn('disks_table', res.context)
        disks_table = res.context['disks_table']
        disks_row = disks_table.data
        # Disk Services
        self.assertEqual(len(disks_row), 2)

        # Table actions
        self.assertEqual(len(disks_table.get_table_actions()), 2)

        # Row actions
        row_actions = disks_table.get_row_actions(disks_row[0])
        self.assertEqual(len(row_actions), 0)
        row_actions = disks_table.get_row_actions(disks_row[1])
        self.assertEqual(len(row_actions), 1)

    @helpers.create_stubs({
        api.azure_api: ('disk_list',
                        'disk_delete',)})
    def test_delete_disk(self):
        api_disk = self.azure_data_disks.list()[1]
        api_disks = self.azure_data_disks.list()

        api.azure_api.disk_list(
            IsA(http.HttpRequest)).AndReturn(api_disks)
        api.azure_api.disk_delete(
            IsA(http.HttpRequest),
            api_disk.name,
            True)

        self.mox.ReplayAll()

        formData = {'action': 'disks__delete__%s' % api_disk.name}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('disk_list',
                        'disk_delete',)})
    def test_delete_disk_exception(self):
        api_disk = self.azure_data_disks.list()[1]
        api_disks = self.azure_data_disks.list()

        api.azure_api.disk_list(
            IsA(http.HttpRequest)).AndReturn(api_disks)
        api.azure_api.disk_delete(
            IsA(http.HttpRequest),
            api_disk.name,
            True).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        formData = {'action': 'disks__delete__%s' % api_disk.name}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)
