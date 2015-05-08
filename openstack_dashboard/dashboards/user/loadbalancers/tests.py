# Copyright 2015 Letv Cloud Computing
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

from socket import timeout as socket_timeout  # noqa

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.user.loadbalancers import tabs
from openstack_dashboard.dashboards.user.loadbalancers import workflows

DASHBOARD = 'user'
PATH_BASE = 'horizon:%s:loadbalancers:' % DASHBOARD

INDEX_URL = reverse(PATH_BASE + 'index')

ADDLOADBALANCER_PATH = PATH_BASE + 'addloadbalancer'
UPDATELOADBALANCER_PATH = PATH_BASE + 'updateloadbalancer'
LOADBALANCER_DETAIL_PATH = PATH_BASE + 'loadbalancerdetails'

ADDLISTENER_PATH = PATH_BASE + 'addlistener'
UPDATELISTENER_PATH = PATH_BASE + 'updatelistener'
LISTENER_DETAIL_PATH = PATH_BASE + 'listenerdetails'

ADDPOOL_PATH = PATH_BASE + 'addpool'
UPDATEPOOL_PATH = PATH_BASE + 'updatepool'
POOL_DETAIL_PATH = PATH_BASE + 'pooldetails'

ADDMEMBER_PATH = PATH_BASE + 'addmember'
UPDATEMEMBER_PATH = PATH_BASE + 'updatemember'

ADDHEALTHMONITOR_PATH = PATH_BASE + 'addhealthmonitor'
UPDATEHEALTHMONITOR_PATH = PATH_BASE + 'updatehealthmonitor'

ADDACL_PATH = PATH_BASE + 'addacl'
UPDATEACL_PATH = PATH_BASE + 'updateacl'

ADDREDUNANCE_PATH = PATH_BASE + 'addredundance'
UPDATEREDUNANCE_PATH = PATH_BASE + 'updateredundance'


class LoadBalancerTests(test.TestCase):
    @test.create_stubs({api.neutron: ('subnet_list',),
                        api.lbaas_v2: (
                            'loadbalancer_list',
                            'pool_list',
                            'listener_list',
                            'healthmonitor_list')})
    def test_index(self):
        subnets = self.subnets.list()
        loadbalancers = self.v2_loadbalancers.list()
        listeners = self.v2_listeners.list()
        pools = self.v2_pools.list()
        healthmonitors = self.v2_healthmonitors.list()

        api.neutron.subnet_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(subnets)
        api.lbaas_v2.loadbalancer_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).MultipleTimes() \
            .AndReturn(loadbalancers)
        api.lbaas_v2.pool_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).MultipleTimes() \
            .AndReturn(pools)
        api.lbaas_v2.listener_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(listeners)
        api.lbaas_v2.healthmonitor_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(healthmonitors)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'user/loadbalancers/index.html')

        self.assertIn('loadbalancers_table', res.context)
        loadbalancers_table = res.context['loadbalancers_table']
        loadbalancers = loadbalancers_table.data
        self.assertEqual(len(loadbalancers), 1)
        row_actions = loadbalancers_table.get_row_actions(loadbalancers[0])
        self.assertEqual(len(row_actions), 3)

        self.assertIn('listeners_table', res.context)
        listeners_table = res.context['listeners_table']
        listeners = listeners_table.data
        self.assertEqual(len(listeners), 1)
        row_actions = listeners_table.get_row_actions(listeners[0])
        self.assertEqual(len(row_actions), 4)

        self.assertIn('pools_table', res.context)
        pools_table = res.context['pools_table']
        pools = pools_table.data
        self.assertEqual(len(pools), 1)
        row_actions = pools_table.get_row_actions(pools[0])
        self.assertEqual(len(row_actions), 4)

        self.assertIn('healthmonitors_table', res.context)
        healthmonitors_table = res.context['healthmonitors_table']
        healthmonitors = healthmonitors_table.data
        self.assertEqual(len(healthmonitors), 1)
        row_actions = healthmonitors_table.get_row_actions(healthmonitors[0])
        self.assertEqual(len(row_actions), 2)

    def _add_loadbalancer_get(self,
                              with_service_type=True,
                              with_provider_exception=False):
        subnet = self.subnets.first()
        default_provider = self.providers.list()[1]['name']

        networks = [{'subnets': [subnet, ]}, ]

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'service-type').AndReturn(with_service_type)
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), self.tenant.id).AndReturn(networks)
        if with_service_type:
            prov_list = api.neutron.provider_list(IsA(http.HttpRequest))
            if with_provider_exception:
                prov_list.AndRaise(self.exceptions.neutron)
            else:
                prov_list.AndReturn(self.providers.list())

        self.mox.ReplayAll()

        res = self.client.get(reverse(ADDLOADBALANCER_PATH))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddLoadbalancer.name)

        expected_objs = ['<AddLoadbalancerStep: addloadbalanceraction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

        if not with_service_type:
            self.assertNotContains(res, default_provider)
            self.assertContains(res, ('Provider for Load Balancer V2 '
                                      'is not supported'))
        elif with_provider_exception:
            self.assertNotContains(res, default_provider)
            self.assertContains(res, 'No provider is available')
        else:
            self.assertContains(res, default_provider)

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'provider_list',
                                      'is_extension_supported')})
    def test_add_loadbalancer_get(self):
        self._add_loadbalancer_get()

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'provider_list',
                                      'is_extension_supported')})
    def test_add_loadbalancer_get_provider_list_exception(self):
        self._add_loadbalancer_get(with_provider_exception=True)

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'is_extension_supported')})
    def test_add_loadbalancer_get_without_service_type_support(self):
        self._add_loadbalancer_get(with_service_type=False)

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_create',),
                        api.neutron: ('network_list_for_tenant',
                                      'provider_list',
                                      'is_extension_supported')})
    def test_add_loadbalancer_post(self):
        loadbalancer = self.v2_loadbalancers.first()
        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), self.tenant.id).AndReturn(networks)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest),
            'service-type').AndReturn(True)
        api.neutron.provider_list(
            IsA(http.HttpRequest)).AndReturn(self.providers.list())
        data = {'name': loadbalancer.name,
                'description': loadbalancer.description,
                'provider': 'haproxy',
                'vip_subnet_id': loadbalancer.vip_subnet_id,
                'vip_address': loadbalancer.vip_address,
                'admin_state_up': loadbalancer.admin_state_up}
        api.lbaas_v2.loadbalancer_create(
            IsA(http.HttpRequest), **data).AndReturn(loadbalancer)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDLOADBALANCER_PATH), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_get',)})
    def test_update_loadbalancer_get(self):
        loadbalancer = self.v2_loadbalancers.first()
        api.lbaas_v2.loadbalancer_get(IsA(http.HttpRequest),
                                      loadbalancer.id).AndReturn(loadbalancer)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATELOADBALANCER_PATH,
                                      args=(loadbalancer.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updateloadbalancer.html')

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_get',
                                       'loadbalancer_update')})
    def test_update_loadbalancer_post(self):
        loadbalancer = self.v2_loadbalancers.first()
        api.lbaas_v2.loadbalancer_get(IsA(http.HttpRequest),
                                      loadbalancer.id).AndReturn(loadbalancer)

        data = {'id': loadbalancer.id,
                'name': loadbalancer.name,
                'description': loadbalancer.description,
                'admin_state_up': loadbalancer.admin_state_up}

        api.lbaas_v2.loadbalancer_update(
            IsA(http.HttpRequest),
            loadbalancer.id, **data).AndReturn(loadbalancer)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(UPDATELOADBALANCER_PATH, args=(loadbalancer.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_get',
                                       'loadbalancer_stats')})
    def test_loadbalancer_detail(self):
        loadbalancer = self.v2_loadbalancers.first()
        stats = self.v2_loadbalancer_stats.first()
        api.lbaas_v2.loadbalancer_get(IsA(http.HttpRequest),
                                      loadbalancer.id).AndReturn(loadbalancer)
        api.lbaas_v2.loadbalancer_stats(IsA(http.HttpRequest),
                                        loadbalancer.id).AndReturn(stats)
        self.mox.ReplayAll()
        res = self.client.get(reverse(LOADBALANCER_DETAIL_PATH,
                                      args=(loadbalancer.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/loadbalancer_detail.html')
        self.assertContains(res, "<dd>haproxy</dd>")
        self.assertContains(res, "<dd>10</dd>")
        self.assertContains(res, "<dd>20</dd>")
        self.assertContains(res, "<dd>30</dd>")
        self.assertContains(res, "<dd>40</dd>")

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_get',
                                       'loadbalancer_stats',
                                       'redundance_list')})
    def test_loadbalancer_detail_redundances_tab(self):
        loadbalancer = self.v2_loadbalancers.first()
        stats = self.v2_loadbalancer_stats.first()
        lbredundances = self.v2_lbredundances.list()
        api.lbaas_v2.loadbalancer_get(IsA(http.HttpRequest),
                                      loadbalancer.id).AndReturn(loadbalancer)
        api.lbaas_v2.loadbalancer_stats(IsA(http.HttpRequest),
                                        loadbalancer.id).AndReturn(stats)
        api.lbaas_v2.redundance_list(
            IsA(http.HttpRequest),
            loadbalancer_id=loadbalancer.id,
            tenant_id=self.tenant.id).AndReturn(lbredundances)
        self.mox.ReplayAll()

        url = reverse(LOADBALANCER_DETAIL_PATH,
                      args=(loadbalancer.id,))
        tg = tabs.LoadbalancerDetailTabs(self.request,
                                         loadbalancer=loadbalancer)
        url += "?%s=%s" % (tg.param_name,
                           tg.get_tab("lbredundances").get_id())

        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'user/loadbalancers/loadbalancer_detail.html')

        self.assertIn('lbredundances_table', res.context)
        lbredundances_table = res.context['lbredundances_table']
        lbredundances = lbredundances_table.data
        self.assertEqual(len(lbredundances), 1)
        row_actions = lbredundances_table.get_row_actions(lbredundances[0])
        self.assertEqual(len(row_actions), 2)

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_list',)})
    def test_add_listener_get(self):
        loadbalancers = self.v2_loadbalancers.list()
        api.lbaas_v2.loadbalancer_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(loadbalancers)
        self.mox.ReplayAll()

        res = self.client.get(reverse(ADDLISTENER_PATH))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddListener.name)

        expected_objs = ['<AddListenerStep: addlisteneraction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas_v2: ('loadbalancer_list',
                                       'listener_create')})
    def test_add_listener_post(self):
        loadbalancers = self.v2_loadbalancers.list()
        listener = self.v2_listeners.first()
        loadbalancer = self.v2_loadbalancers.first()
        data = {'name': listener.name,
                'description': listener.description,
                'loadbalancer_id': loadbalancer.id,
                'protocol': listener.protocol,
                'protocol_port': listener.protocol_port,
                'connection_limit': '5000',
                'admin_state_up': listener.admin_state_up}
        api.lbaas_v2.loadbalancer_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(loadbalancers)
        api.lbaas_v2.listener_create(
            IsA(http.HttpRequest), **data).AndReturn(listener)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDLISTENER_PATH), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('listener_get',)})
    def test_update_listener_get(self):
        listener = self.v2_listeners.first()
        api.lbaas_v2.listener_get(IsA(http.HttpRequest),
                                  listener.id).AndReturn(listener)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATELISTENER_PATH,
                                      args=(listener.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updatelistener.html')

    @test.create_stubs({api.lbaas_v2: ('listener_get',
                                       'listener_update')})
    def test_update_listener_post(self):
        listener = self.v2_listeners.first()
        api.lbaas_v2.listener_get(IsA(http.HttpRequest),
                                  listener.id).AndReturn(listener)

        data = {'id': listener.id,
                'name': listener.name,
                'description': listener.description,
                'connection_limit': '5000',
                'admin_state_up': listener.admin_state_up}

        api.lbaas_v2.listener_update(
            IsA(http.HttpRequest),
            listener.id, **data).AndReturn(listener)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(UPDATELISTENER_PATH, args=(listener.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('listener_get',)})
    def test_listener_detail(self):
        listener = self.v2_listeners.first()
        api.lbaas_v2.listener_get(IsA(http.HttpRequest),
                                  listener.id).AndReturn(listener)
        self.mox.ReplayAll()
        res = self.client.get(reverse(LISTENER_DETAIL_PATH,
                                      args=(listener.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/listener_detail.html')
        self.assertContains(res, "<dt>Protocol</dt>")
        self.assertContains(res, "<dd>-1</dd>")
        self.assertContains(res, "<dd>TCP</dd>")

    @test.create_stubs({api.lbaas_v2: ('listener_get',
                                       'acl_list')})
    def test_listener_detail_acl_tab(self):
        listener = self.v2_listeners.first()
        acls = self.v2_acls.list()
        api.lbaas_v2.listener_get(IsA(http.HttpRequest),
                                  listener.id).AndReturn(listener)
        api.lbaas_v2.acl_list(IsA(http.HttpRequest),
                              listener_id=listener.id,
                              tenant_id=self.tenant.id).AndReturn(acls)
        self.mox.ReplayAll()
        url = reverse(LISTENER_DETAIL_PATH,
                      args=(listener.id,))
        tg = tabs.ListenerDetailTabs(self.request, listener=listener)
        url += "?%s=%s" % (tg.param_name, tg.get_tab("acls").get_id())

        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'user/loadbalancers/listener_detail.html')

        self.assertIn('acls_table', res.context)
        acls_table = res.context['acls_table']
        acls = acls_table.data
        self.assertEqual(len(acls), 1)
        row_actions = acls_table.get_row_actions(acls[0])
        self.assertEqual(len(row_actions), 2)

    @test.create_stubs({api.lbaas_v2: ('listener_list',)})
    def test_add_pool_get(self):
        listeners = self.v2_listeners.list()
        api.lbaas_v2.listener_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(listeners)
        self.mox.ReplayAll()

        res = self.client.get(reverse(ADDPOOL_PATH))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddPool.name)

        expected_objs = ['<AddPoolStep: addpoolaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas_v2: ('listener_list',
                                       'pool_create')})
    def test_add_pool_post(self):
        listeners = self.v2_listeners.list()
        listener = self.v2_listeners.first()
        pool = self.v2_pools.first()
        data = {'name': pool.name,
                'description': pool.description,
                'listener_id': listener.id,
                'lb_algorithm': pool.lb_algorithm,
                'protocol': pool.protocol,
                'admin_state_up': pool.admin_state_up}
        api.lbaas_v2.listener_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(listeners)
        api.lbaas_v2.pool_create(
            IsA(http.HttpRequest), **data).AndReturn(pool)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDPOOL_PATH), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('pool_get',)})
    def test_update_pool_get(self):
        pool = self.v2_pools.first()
        api.lbaas_v2.pool_get(IsA(http.HttpRequest),
                              pool.id).AndReturn(pool)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATEPOOL_PATH,
                              args=(pool.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updatepool.html')

    @test.create_stubs({api.lbaas_v2: ('pool_get',
                                       'pool_update')})
    def test_update_pool_post(self):
        pool = self.v2_pools.first()
        api.lbaas_v2.pool_get(IsA(http.HttpRequest),
                              pool.id).AndReturn(pool)
        data = {'id': pool.id,
                'name': pool.name,
                'description': pool.description,
                'lb_algorithm': pool.lb_algorithm,
                'admin_state_up': pool.admin_state_up}

        api.lbaas_v2.pool_update(
            IsA(http.HttpRequest),
            pool.id, **data).AndReturn(pool)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(UPDATEPOOL_PATH, args=(pool.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('pool_get',)})
    def test_pool_detail(self):
        pool = self.v2_pools.first()
        api.lbaas_v2.pool_get(IsA(http.HttpRequest),
                              pool.id).AndReturn(pool)
        self.mox.ReplayAll()
        res = self.client.get(reverse(POOL_DETAIL_PATH,
                                      args=(pool.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/pool_detail.html')
        self.assertContains(res, "<dt>Algorithm</dt>")
        self.assertContains(res, "<dd>ROUND_ROBIN</dd>")

    @test.create_stubs({api.lbaas_v2: ('pool_get',
                                       'member_list')})
    def test_pool_detail_member_tab(self):
        pool = self.v2_pools.first()
        members = self.v2_members.list()
        api.lbaas_v2.pool_get(IsA(http.HttpRequest),
                              pool.id).AndReturn(pool)
        api.lbaas_v2.member_list(IsA(http.HttpRequest),
                                 pool=pool.id,
                                 pool_id=pool.id,
                                 tenant_id=self.tenant.id).AndReturn(members)
        self.mox.ReplayAll()
        url = reverse(POOL_DETAIL_PATH,
                      args=(pool.id,))
        tg = tabs.PoolDetailTabs(self.request, pool=pool)
        url += "?%s=%s" % (tg.param_name, tg.get_tab("members").get_id())

        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'user/loadbalancers/pool_detail.html')

        self.assertIn('members_table', res.context)
        members_table = res.context['members_table']
        members = members_table.data
        self.assertEqual(len(members), 2)
        row_actions = members_table.get_row_actions(members[0])
        self.assertEqual(len(row_actions), 2)

    @test.create_stubs({api.lbaas_v2: ('pool_list',)})
    def test_add_healthmonitor_get(self):
        pools = self.v2_pools.list()
        api.lbaas_v2.pool_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(pools)
        self.mox.ReplayAll()

        res = self.client.get(reverse(ADDHEALTHMONITOR_PATH))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddHealthmonitor.name)

        expected_objs = ['<AddHealthmonitorStep: addhealthmonitoraction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas_v2: ('pool_list',
                                       'healthmonitor_create')})
    def test_add_healthmonitor_post(self):
        pools = self.v2_pools.list()
        healthmonitor = self.v2_healthmonitors.first()
        pool = self.v2_pools.first()
        data = {'pool_id': pool.id,
                'type': 'ping',
                'delay': healthmonitor.delay,
                'timeout': healthmonitor.timeout,
                'max_retries': healthmonitor.max_retries,
                'http_method': healthmonitor.http_method,
                'url_path': healthmonitor.url_path,
                'expected_codes': healthmonitor.expected_codes,
                'admin_state_up': healthmonitor.admin_state_up}
        api.lbaas_v2.pool_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(pools)
        api.lbaas_v2.healthmonitor_create(
            IsA(http.HttpRequest), **data).AndReturn(healthmonitor)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDHEALTHMONITOR_PATH), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('healthmonitor_get',)})
    def test_update_healthmonitor_get(self):
        healthmonitor = self.v2_healthmonitors.first()
        api.lbaas_v2.healthmonitor_get(
            IsA(http.HttpRequest),
            healthmonitor.id).AndReturn(healthmonitor)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATEHEALTHMONITOR_PATH,
                              args=(healthmonitor.id,)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updatehealthmonitor.html')

    @test.create_stubs({api.lbaas_v2: ('healthmonitor_get',
                                       'healthmonitor_update')})
    def test_update_healthmonitor_post(self):
        healthmonitor = self.v2_healthmonitors.first()
        api.lbaas_v2.healthmonitor_get(
            IsA(http.HttpRequest),
            healthmonitor.id).AndReturn(healthmonitor)
        data = {'healthmonitor_id': healthmonitor.id,
                'type': 'ping',
                'delay': healthmonitor.delay,
                'timeout': healthmonitor.timeout,
                'max_retries': healthmonitor.max_retries,
                'http_method': healthmonitor.http_method,
                'url_path': healthmonitor.url_path,
                'expected_codes': healthmonitor.expected_codes,
                'admin_state_up': healthmonitor.admin_state_up}

        api.lbaas_v2.healthmonitor_update(
            IsA(http.HttpRequest),
            **data).AndReturn(healthmonitor)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(UPDATEHEALTHMONITOR_PATH, args=(healthmonitor.id,)), data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.lbaas_v2: ('pool_list',),
                        api.neutron: ('network_list_for_tenant',)})
    def test_add_member_get(self):
        pool = self.v2_pools.first()
        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), self.tenant.id).AndReturn(networks)
        self.mox.ReplayAll()

        res = self.client.get(reverse(ADDMEMBER_PATH, args=(pool.id,)))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddMember.name)

        expected_objs = ['<AddMemberStep: addmemberaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas_v2: ('member_create',),
                        api.neutron: ('network_list_for_tenant',)})
    def test_add_member_post(self):
        pool = self.v2_pools.first()
        member = self.v2_members.first()
        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), self.tenant.id).AndReturn(networks)
        data = {'pool_id': pool.id,
                'protocol_port': member.protocol_port,
                'weight': member.weight,
                'subnet_id': member.subnet_id,
                'address': member.address,
                'admin_state_up': member.admin_state_up}
        api.lbaas_v2.member_create(
            IsA(http.HttpRequest), **data).AndReturn(member)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDMEMBER_PATH, args=(pool.id,)), data)

        self.assertNoFormErrors(res)
        expected_url = reverse(POOL_DETAIL_PATH, args=(pool.id,))
        self.assertRedirects(res, expected_url, 302, 302)

    @test.create_stubs({api.lbaas_v2: ('member_get',)})
    def test_update_member_get(self):
        pool = self.v2_pools.first()
        member = self.v2_members.first()
        api.lbaas_v2.member_get(IsA(http.HttpRequest),
                                member.id,
                                pool.id).AndReturn(member)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATEMEMBER_PATH,
                              args=(pool.id,
                                    member.id)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updatemember.html')

    @test.create_stubs({api.lbaas_v2: ('member_get',
                                       'member_update')})
    def test_update_member_post(self):
        pool = self.v2_pools.first()
        member = self.v2_members.first()
        api.lbaas_v2.member_get(IsA(http.HttpRequest),
                                member.id,
                                pool.id).AndReturn(member)
        data = {'member_id': member.id,
                'pool_id': pool.id,
                'weight': member.weight,
                'admin_state_up': member.admin_state_up}

        api.lbaas_v2.member_update(
            IsA(http.HttpRequest),
            **data).AndReturn(member)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(UPDATEMEMBER_PATH,
                    args=(pool.id,
                          member.id)),
            data)

        self.assertNoFormErrors(res)
        expected_url = reverse(POOL_DETAIL_PATH, args=(pool.id,))
        self.assertRedirects(res, expected_url, 302, 302)

    def test_add_acl_get(self):
        listener = self.v2_listeners.first()
        self.mox.ReplayAll()
        res = self.client.get(reverse(ADDACL_PATH, args=(listener.id,)))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddAcl.name)

        expected_objs = ['<AddAclStep: addaclaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas_v2: ('acl_create',)})
    def test_add_acl_post(self):
        listener = self.v2_listeners.first()
        acl = self.v2_acls.first()
        data = {'listener_id': acl.listener_id,
                'name': acl.name,
                'description': acl.description,
                'action': acl.action,
                'condition': acl.condition,
                'acl_type': acl.acl_type,
                'operator': acl.operator,
                'match': acl.match,
                'match_condition': acl.match_condition,
                'admin_state_up': acl.admin_state_up}
        api.lbaas_v2.acl_create(
            IsA(http.HttpRequest), **data).AndReturn(acl)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDACL_PATH, args=(listener.id,)), data)

        self.assertNoFormErrors(res)
        expected_url = reverse(LISTENER_DETAIL_PATH, args=(listener.id,))
        self.assertRedirects(res, expected_url, 302, 302)

    @test.create_stubs({api.lbaas_v2: ('acl_get',)})
    def test_update_acl_get(self):
        listener = self.v2_listeners.first()
        acl = self.v2_acls.first()
        api.lbaas_v2.acl_get(IsA(http.HttpRequest),
                             acl.id).AndReturn(acl)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATEACL_PATH,
                              args=(listener.id,
                                    acl.id)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updateacl.html')

    @test.create_stubs({api.lbaas_v2: ('acl_get',
                                       'acl_update')})
    def test_update_acl_post(self):
        listener = self.v2_listeners.first()
        acl = self.v2_acls.first()
        api.lbaas_v2.acl_get(IsA(http.HttpRequest),
                             acl.id).AndReturn(acl)
        data = {'listener_id': acl.listener_id,
                'acl_id': acl.id,
                'name': acl.name,
                'description': acl.description,
                'action': acl.action,
                'condition': acl.condition,
                'acl_type': acl.acl_type,
                'operator': acl.operator,
                'match': acl.match,
                'match_condition': acl.match_condition,
                'admin_state_up': acl.admin_state_up}

        api.lbaas_v2.acl_update(
            IsA(http.HttpRequest),
            **data).AndReturn(acl)

        self.mox.ReplayAll()

        res = self.client.post(reverse(UPDATEACL_PATH,
                                       args=(listener.id,
                                             acl.id)),
                               data)

        self.assertNoFormErrors(res)
        expected_url = reverse(LISTENER_DETAIL_PATH, args=(listener.id,))
        self.assertRedirects(res, expected_url, 302, 302)

    def test_add_redundance_get(self):
        loadbalancer = self.v2_loadbalancers.first()
        self.mox.ReplayAll()
        res = self.client.get(reverse(ADDREDUNANCE_PATH,
                                      args=(loadbalancer.id,)))
        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddRedundance.name)

        expected_objs = ['<AddRedundanceStep: addredundanceaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas_v2: ('redundance_create',)})
    def test_add_redundance_post(self):
        loadbalancer = self.v2_loadbalancers.first()
        redundance = self.v2_lbredundances.first()
        data = {'loadbalancer_id': loadbalancer.id,
                'name': redundance.name,
                'agent_id': None,
                'description': redundance.description,
                'admin_state_up': redundance.admin_state_up}
        api.lbaas_v2.redundance_create(
            IsA(http.HttpRequest),
            **data).AndReturn(redundance)

        self.mox.ReplayAll()

        res = self.client.post(
            reverse(ADDREDUNANCE_PATH,
                    args=(loadbalancer.id,)),
            data)

        self.assertNoFormErrors(res)
        expected_url = reverse(LOADBALANCER_DETAIL_PATH,
                               args=(loadbalancer.id,))
        self.assertRedirects(res, expected_url, 302, 302)

    @test.create_stubs({api.lbaas_v2: ('redundance_get',)})
    def test_update_redundance_get(self):
        loadbalancer = self.v2_loadbalancers.first()
        redundance = self.v2_lbredundances.first()
        api.lbaas_v2.redundance_get(IsA(http.HttpRequest),
                                    redundance.id,
                                    loadbalancer.id).AndReturn(redundance)
        self.mox.ReplayAll()
        res = self.client.get(reverse(UPDATEREDUNANCE_PATH,
                              args=(loadbalancer.id,
                                    redundance.id)))
        self.assertTemplateUsed(res,
                                'user/loadbalancers/updateredundance.html')

    @test.create_stubs({api.lbaas_v2: ('redundance_get',
                                       'redundance_update')})
    def test_update_redundance_post(self):
        loadbalancer = self.v2_loadbalancers.first()
        redundance = self.v2_lbredundances.first()
        api.lbaas_v2.redundance_get(IsA(http.HttpRequest),
                                    redundance.id,
                                    loadbalancer.id).AndReturn(redundance)
        data = {'redundance_id': redundance.id,
                'loadbalancer_id': loadbalancer.id,
                'refresh': 'false',
                'name': redundance.name,
                'description': redundance.description,
                'admin_state_up': redundance.admin_state_up}

        api.lbaas_v2.redundance_update(
            IsA(http.HttpRequest),
            **data).AndReturn(redundance)

        self.mox.ReplayAll()

        res = self.client.post(reverse(UPDATEREDUNANCE_PATH,
                                       args=(loadbalancer.id,
                                             redundance.id)),
                               data)

        self.assertNoFormErrors(res)
        expected_url = reverse(LOADBALANCER_DETAIL_PATH,
                               args=(loadbalancer.id,))
        self.assertRedirects(res, expected_url, 302, 302)

    @test.create_stubs({api.neutron: ('subnet_list',),
                        api.lbaas_v2: (
                            'loadbalancer_list',
                            'loadbalancer_delete')})
    def test_delete_loadbalancer(self):
        subnets = self.subnets.list()
        loadbalancers = self.v2_loadbalancers.list()
        loadbalancer = self.v2_loadbalancers.first()

        api.neutron.subnet_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(subnets)
        api.lbaas_v2.loadbalancer_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id).MultipleTimes() \
            .AndReturn(loadbalancers)

        api.lbaas_v2.loadbalancer_delete(IsA(http.HttpRequest),
                                         loadbalancer.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "loadbalancers__deleteloadbalancer__%s" % loadbalancer.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.lbaas_v2: ('listener_list',
                                       'listener_delete')})
    def test_delete_listener(self):
        listeners = self.v2_listeners.list()
        listener = self.v2_listeners.first()

        api.lbaas_v2.listener_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(listeners)

        api.lbaas_v2.listener_delete(IsA(http.HttpRequest),
                                     listener.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "listeners__deletelistener__%s" % listener.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.lbaas_v2: ('pool_list',
                                       'pool_delete')})
    def test_delete_pool(self):
        pools = self.v2_pools.list()
        pool = self.v2_pools.first()

        api.lbaas_v2.pool_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(pools)

        api.lbaas_v2.pool_delete(IsA(http.HttpRequest),
                                 pool.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "pools__deletepool__%s" % pool.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.lbaas_v2: ('healthmonitor_list',
                                       'healthmonitor_delete')})
    def test_delete_healthmonitor(self):
        healthmonitors = self.v2_healthmonitors.list()
        healthmonitor = self.v2_healthmonitors.first()

        api.lbaas_v2.healthmonitor_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id) \
            .AndReturn(healthmonitors)

        api.lbaas_v2.healthmonitor_delete(IsA(http.HttpRequest),
                                          healthmonitor.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "healthmonitors__deletehealthmonitor__%s" % healthmonitor.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.lbaas_v2: ('acl_list',
                                       'acl_delete',
                                       'listener_get')})
    def test_delete_acl(self):
        acls = self.v2_acls.list()
        acl = self.v2_acls.first()
        listener = self.v2_listeners.first()

        api.lbaas_v2.listener_get(
            IsA(http.HttpRequest),
            listener.id)
        api.lbaas_v2.acl_list(
            IsA(http.HttpRequest),
            listener_id=listener.id,
            tenant_id=self.tenant.id) \
            .AndReturn(acls)

        api.lbaas_v2.acl_delete(IsA(http.HttpRequest),
                                acl.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "acls__deleteacl__%s" % acl.id}
        res = self.client.post(
            reverse(LISTENER_DETAIL_PATH, args=(listener.id,)), form_data)

        self.assertNoFormErrors(res)

    @test.create_stubs({api.lbaas_v2: ('member_list',
                                       'member_delete',
                                       'pool_get')})
    def test_delete_member(self):
        members = self.v2_members.list()
        member = self.v2_members.first()
        pool = self.v2_pools.first()

        api.lbaas_v2.pool_get(
            IsA(http.HttpRequest),
            pool.id)
        api.lbaas_v2.member_list(
            IsA(http.HttpRequest),
            pool=pool.id,
            pool_id=pool.id,
            tenant_id=self.tenant.id) \
            .AndReturn(members)

        api.lbaas_v2.member_delete(IsA(http.HttpRequest),
                                   member.id,
                                   pool.id)
        self.mox.ReplayAll()

        form_data = {
            "action":
            "members__deletemember__%s" % member.id}
        res = self.client.post(
            reverse(POOL_DETAIL_PATH, args=(pool.id,)), form_data)

        self.assertNoFormErrors(res)
