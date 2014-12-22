# Copyright 2014 Letv Cloud Computing
# All Rights Reserved.
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

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:admin:floating_ips:index')


class AdminFloatingIpViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.network: ('tenant_floating_ip_list', ),
                        api.nova: ('server_list', ),
                        api.keystone: ('tenant_list', ),
                        api.neutron: ('network_list', )})
    def test_index(self):
        # Use neutron test data
        fips = self.q_floating_ips_with_instance.list()
        servers = self.servers.list()
        tenants = self.tenants.list()
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn(fips)
        api.nova.server_list(IsA(http.HttpRequest), all_tenants=True) \
            .AndReturn([servers, False])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {"router:external": True}
        api.neutron.network_list(IsA(http.HttpRequest), **params) \
            .AndReturn(self.networks.list())

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/floating_ips/index.html')
        self.assertIn('floating_ips_table', res.context)
        floating_ips_table = res.context['floating_ips_table']
        floating_ips = floating_ips_table.data
        self.assertEqual(len(floating_ips), 2)

        row_actions = floating_ips_table.get_row_actions(floating_ips[0])
        self.assertEqual(len(row_actions), 1)
        row_actions = floating_ips_table.get_row_actions(floating_ips[1])
        self.assertEqual(len(row_actions), 2)

    @test.create_stubs({api.network: ('tenant_floating_ip_get',)})
    def test_floating_ip_detail_get(self):
        fip = self.q_floating_ips_with_instance.first()
        api.network.tenant_floating_ip_get(
            IsA(http.HttpRequest),
            fip.id).AndReturn(self.q_floating_ips_with_instance.first())
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:floating_ips:detail',
                                      args=[fip.id]))
        self.assertTemplateUsed(res,
                                'admin/floating_ips/detail.html')
        self.assertEqual(res.context['floating_ip'].ip, fip.ip)
        self.assertContains(res, "<h1>Floating IP Details</h1>",
                            1, 200)

    @test.create_stubs({api.network: ('tenant_floating_ip_get',)})
    def test_floating_ip_detail_exception(self):
        fip = self.q_floating_ips_with_instance.first()
        # Only supported by neutron, so raise a neutron exception
        api.network.tenant_floating_ip_get(
            IsA(http.HttpRequest),
            fip.id).AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:floating_ips:detail',
                                      args=[fip.id]))

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.network: ('tenant_floating_ip_list', )})
    def test_index_no_floating_ips(self):
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn([])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/floating_ips/index.html')

    @test.create_stubs({api.network: ('tenant_floating_ip_list', )})
    def test_index_error(self):
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True) \
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/floating_ips/index.html')

    @test.create_stubs({api.network: ('floating_ip_pools_list', ),
                        api.keystone: ('tenant_list', )})
    def test_admin_allocate_get(self):
        tenants = self.tenants.list()
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn(self.pools.list())
        self.mox.ReplayAll()

        url = reverse('horizon:admin:floating_ips:allocate')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'admin/floating_ips/allocate.html')
        allocate_form = res.context['form']

        pool_choices = allocate_form.fields['pool'].choices
        self.assertEqual(len(pool_choices), 2)
        tenant_choices = allocate_form.fields['tenant'].choices
        self.assertEqual(len(tenant_choices), 3)

    @test.create_stubs({api.network: ('tenant_floating_ip_list', ),
                        api.nova: ('server_list', ),
                        api.keystone: ('tenant_list', ),
                        api.neutron: ('network_list', )})
    def test_floating_ip_table_actions(self):
        # Use neutron test data
        fips = self.q_floating_ips_with_instance.list()
        servers = self.servers.list()
        tenants = self.tenants.list()
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest),
                                            all_tenants=True).AndReturn(fips)
        api.nova.server_list(IsA(http.HttpRequest), all_tenants=True) \
            .AndReturn([servers, False])
        api.keystone.tenant_list(IsA(http.HttpRequest))\
            .AndReturn([tenants, False])
        params = {"router:external": True}
        api.neutron.network_list(IsA(http.HttpRequest), **params) \
            .AndReturn(self.networks.list())

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'admin/floating_ips/index.html')
        self.assertIn('floating_ips_table', res.context)
        floating_ips_table = res.context['floating_ips_table']
        floating_ips = floating_ips_table.data
        self.assertEqual(len(floating_ips), 2)
        # table actions
        self.assertContains(res, 'id="floating_ips__action_allocate"')
        self.assertContains(res, 'id="floating_ips__action_delete"')
        # row actions
        self.assertContains(res, 'floating_ips__delete__%s' % fips[0].id)
        self.assertContains(res, 'floating_ips__delete__%s' % fips[1].id)
        self.assertContains(res, 'floating_ips__disassociate__%s' % fips[1].id)
