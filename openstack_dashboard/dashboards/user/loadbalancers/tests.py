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

    """
    ADDLISTENER_PATH = PATH_BASE + 'addlistener'
    UPDATELISTENER_PATH = PATH_BASE + 'updatelistener'
    LISTENER_DETAIL_PATH = PATH_BASE + 'listenerdetails'

        name = forms.CharField(max_length=80, label=_("Name"))
        description = forms.CharField(
            initial="", required=False,
            max_length=80, label=_("Description"))

        loadbalancer_id = forms.ChoiceField(label=_("Loadbalancer"))

        protocol = forms.ChoiceField(label=_("Protocol"))
        protocol_port = forms.IntegerField(
            label=_("Protocol Port"), min_value=1,
            help_text=_("Enter an integer value "
                        "between 1 and 65535."),
            validators=[validators.validate_port_range])

        connection_limit = forms.ChoiceField(
            choices=[(5000, 5000),
                     (10000, 10000),
                     (20000, 20000),
                     (40000, 40000)],
            label=_("Connection Limit"),
            help_text=_("Maximum number of connections allowed."))

        admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                    (False, _('DOWN'))],
                                           label=_("Admin State"))
    """
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
