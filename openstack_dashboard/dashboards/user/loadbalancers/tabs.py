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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api

from openstack_dashboard.dashboards.user.loadbalancers\
    import tables as l_tables
from openstack_dashboard.dashboards.user.loadbalancers\
    import utils


class LoadbalancersTab(tabs.TableTab):
    table_classes = (l_tables.LoadbalancerTable,)
    name = _("Loadbalancers")
    slug = "loadbalancers_tab"
    template_name = "horizon/common/_detail_table.html"
    permissions = ('openstack.services.network',)

    def get_loadbalancers_data(self):
        tenant_id = self.request.user.tenant_id
        subnet_dict = dict([(
            n.id, n.cidr) for n in utils.get_subnets(self.request,
                                                     tenant_id)])
        loadbalancers = utils.get_loadbalancers(self.request,
                                                tenant_id)
        if subnet_dict and loadbalancers:
            for lb in loadbalancers:
                lb.subnet_name = subnet_dict.get(lb.vip_subnet_id)
        return loadbalancers


class ListenersTab(tabs.TableTab):
    table_classes = (l_tables.ListenersTable,)
    name = _("Listeners")
    slug = "listeners"
    template_name = "horizon/common/_detail_table.html"

    def get_listeners_data(self):
        tenant_id = self.request.user.tenant_id
        loadbalancer_dict = dict([(
            l.id, l.name) for l in utils.get_loadbalancers(self.request,
                                                           tenant_id)])
        pool_dict = dict([(
            p.id, p.name) for p in utils.get_pools(self.request,
                                                   tenant_id)])
        listeners = utils.get_listeners(self.request,
                                        tenant_id)

        if loadbalancer_dict and pool_dict:
            for ls in listeners:
                # NOTE(yulong): Returning a list to
                # future proof for M:N objects
                # that are not yet implemented.
                # Neutron-lbaas-v2 not implemented
                ls.loadbalancer_name = loadbalancer_dict.get(
                    ls.loadbalancers[0]['id'])
                ls.pool_name = pool_dict.get(ls.default_pool_id)
        return listeners


class PoolsTab(tabs.TableTab):
    table_classes = (l_tables.PoolsTable,)
    name = _("Pools")
    slug = "pools"
    template_name = "horizon/common/_detail_table.html"

    def get_pools_data(self):
        tenant_id = self.request.user.tenant_id
        return utils.get_pools(self.request, tenant_id)


class HealthmonitorsTab(tabs.TableTab):
    table_classes = (l_tables.HealthmonitorsTable,)
    name = _("Healthmonitors")
    slug = "healthmonitors_tab"
    template_name = "horizon/common/_detail_table.html"
    permissions = ('openstack.services.network',)

    def get_healthmonitors_data(self):
        tenant_id = self.request.user.tenant_id
        return utils.get_healthmonitors(self.request, tenant_id)


class LoadbalancerTabs(tabs.TabGroup):
    slug = "loadbalancer_tabs"
    tabs = (LoadbalancersTab,
            ListenersTab,
            PoolsTab,
            HealthmonitorsTab)
    sticky = True


class LoadbalancerOverviewTab(tabs.Tab):
    name = _("LoadbalancerOverview")
    slug = "loadbalanceroverview"
    template_name = "user/loadbalancers/_loadbalancer_details.html"

    def get_context_data(self, request):
        return {"loadbalancer": self.tab_group.kwargs['loadbalancer']}


class LbRedundancesTab(tabs.TableTab):
    table_classes = (l_tables.LbRedundancesTable,)
    name = _("Loadbalancer Redundances")
    slug = "lbredundances"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_lbredundances_data(self):
        loadbalancer_id = self.tab_group.kwargs['loadbalancer_id']
        tenant_id = self.request.user.tenant_id
        try:
            lbredundances = api.lbaas_v2.redundance_list(
                self.request,
                loadbalancer_id=loadbalancer_id,
                tenant_id=tenant_id)
        except Exception:
            lbredundances = []
            exceptions.handle(
                self.request,
                _('Unable to retrieve loadbalancer redundance list.'))
        return lbredundances


class LoadbalancerDetailTabs(tabs.TabGroup):
    slug = "loadbalancer_details"
    tabs = (LoadbalancerOverviewTab,
            LbRedundancesTab)
    sticky = True


class AclsTab(tabs.TableTab):
    table_classes = (l_tables.AclsTable,)
    name = _("Acls")
    slug = "acls"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_acls_data(self):
        listener_id = self.tab_group.kwargs['listener_id']
        tenant_id = self.request.user.tenant_id
        try:
            acls = api.lbaas_v2.acl_list(self.request,
                                         listener_id=listener_id,
                                         tenant_id=tenant_id)
        except Exception:
            acls = []
            exceptions.handle(self.request,
                              _('Unable to retrieve acl list.'))
        return acls


class ListenerOverviewTab(tabs.Tab):
    name = _("ListenerOverview")
    slug = "listeneroverview"
    template_name = "user/loadbalancers/_listener_details.html"

    def get_context_data(self, request):
        return {"listener": self.tab_group.kwargs['listener']}


class ListenerDetailTabs(tabs.TabGroup):
    slug = "listener_details"
    tabs = (ListenerOverviewTab, AclsTab,)
    sticky = True


class MembersTab(tabs.TableTab):
    table_classes = (l_tables.MembersTable,)
    name = _("Members")
    slug = "members"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_members_data(self):
        tenant_id = self.request.user.tenant_id
        pool_id = self.tab_group.kwargs['pool_id']
        try:
            members = api.lbaas_v2.member_list(self.request,
                                               pool=pool_id,
                                               pool_id=pool_id,
                                               tenant_id=tenant_id)
            for m in members:
                m.pool_id = pool_id
        except Exception:
            members = []
            exceptions.handle(self.request,
                              _('Unable to retrieve member list.'))
        return members


class PoolOverviewTab(tabs.Tab):
    name = _("PoolOverview")
    slug = "pooloverview"
    template_name = "user/loadbalancers/_pool_details.html"

    def get_context_data(self, request):
        return {"pool": self.tab_group.kwargs['pool']}


class PoolDetailTabs(tabs.TabGroup):
    slug = "member_details"
    tabs = (PoolOverviewTab, MembersTab,)
    sticky = True
