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

from openstack_dashboard.dashboards.manager.loadbalancers\
    import tables as l_tables
from openstack_dashboard.dashboards.manager.loadbalancers\
    import utils


class LoadbalancersTab(tabs.TableTab):
    table_classes = (l_tables.LoadbalancerTable,)
    name = _("Loadbalancers")
    slug = "loadbalancers_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_loadbalancers_data(self):
        subnet_dict = dict([(
            n.id, n.cidr) for n in utils.get_subnets(self.request)])
        tenant_dict = utils.get_tenants(self.request)
        loadbalancers = utils.get_loadbalancers(self.request)
        if subnet_dict and tenant_dict and loadbalancers:
            for lb in loadbalancers:
                lb.subnet_name = subnet_dict.get(lb.vip_subnet_id)
                tenant = tenant_dict.get(lb.tenant_id, None)
                lb.tenant_name = getattr(tenant, 'name', None)
        return loadbalancers


class ListenersTab(tabs.TableTab):
    table_classes = (l_tables.ListenersTable,)
    name = _("Listeners")
    slug = "listeners_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_listeners_data(self):
        loadbalancer_dict = dict([(
            l.id, l.name) for l in utils.get_loadbalancers(self.request)])
        tenant_dict = utils.get_tenants(self.request)
        pool_dict = dict([(
            p.id, p.name) for p in utils.get_pools(self.request)])
        listeners = utils.get_listeners(self.request)

        if loadbalancer_dict and tenant_dict and pool_dict and listeners:
            for ls in listeners:
                # NOTE(yulong): Returning a list to
                # future proof for M:N objects
                # that are not yet implemented.
                # Neutron-lbaas-v2 not implemented
                ls.loadbalancer_name = loadbalancer_dict.get(
                    ls.loadbalancers[0]['id'])
                ls.pool_name = pool_dict.get(ls.default_pool_id)
                tenant = tenant_dict.get(ls.tenant_id, None)
                ls.tenant_name = getattr(tenant, 'name', None)
        return listeners


class PoolsTab(tabs.TableTab):
    table_classes = (l_tables.PoolsTable,)
    name = _("Pools")
    slug = "pools_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_pools_data(self):
        tenant_dict = utils.get_tenants(self.request)
        pools = utils.get_pools(self.request)
        if tenant_dict and pools:
            for pl in pools:
                tenant = tenant_dict.get(pl.tenant_id, None)
                pl.tenant_name = getattr(tenant, 'name', None)
        return pools


class HealthmonitorsTab(tabs.TableTab):
    table_classes = (l_tables.HealthmonitorsTable,)
    name = _("Healthmonitors")
    slug = "healthmonitors_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_healthmonitors_data(self):
        tenant_dict = utils.get_tenants(self.request)
        hms = utils.get_healthmonitors(self.request)
        if tenant_dict and hms:
            for hm in hms:
                tenant = tenant_dict.get(hm.tenant_id, None)
                hm.tenant_name = getattr(tenant, 'name', None)
        return hms


class LVSPortTab(tabs.TableTab):
    table_classes = (l_tables.LVSPortsTable,)
    name = _("LVS Ports")
    slug = "lvsports_tab"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_lvsports_data(self):
        tenant_dict = utils.get_tenants(self.request)
        subnet_dict = dict([(
            n.id, n.cidr) for n in utils.get_subnets(self.request)])
        loadbalancer_dict = dict([(
            l.id, l.name) for l in utils.get_loadbalancers(self.request)])
        try:
            lvsports = api.lbaas_v2.lvsport_list(
                self.request)
        except Exception:
            lvsports = []
            exceptions.handle(
                self.request,
                _('Unable to retrieve loadbalancer LVS Port list.'))

        if lvsports:
            if subnet_dict and lvsports:
                for lv in lvsports:
                    tenant = tenant_dict.get(lv.tenant_id, None)
                    lv.tenant_name = getattr(tenant, 'name', None)
                    lv.loadbalancer_name = loadbalancer_dict.get(
                        lv.loadbalancer_id)
                    lv.subnet_name = subnet_dict.get(lv.subnet_id)
        return lvsports


class LoadbalancerTabs(tabs.TabGroup):
    slug = "loadbalancer_tabs"
    tabs = (LoadbalancersTab,
            ListenersTab,
            PoolsTab,
            HealthmonitorsTab,
            LVSPortTab)
    sticky = True


class LoadbalancerOverviewTab(tabs.Tab):
    name = _("Loadbalancer Overview")
    slug = "loadbalanceroverview"
    template_name = "manager/loadbalancers/_loadbalancer_details.html"

    def get_context_data(self, request):
        return {"loadbalancer": self.tab_group.kwargs['loadbalancer']}


class LbRedundancesTab(tabs.TableTab):
    table_classes = (l_tables.LbRedundancesTable,)
    name = _("Loadbalancer Redundances")
    slug = "lbredundances_tab"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_lbredundances_data(self):
        loadbalancer_id = self.tab_group.kwargs['loadbalancer_id']
        try:
            lbredundances = api.lbaas_v2.redundance_list(
                self.request,
                loadbalancer_id=loadbalancer_id)
        except Exception:
            lbredundances = []
            exceptions.handle(
                self.request,
                _('Unable to retrieve loadbalancer redundance list.'))
        tenant_dict = utils.get_tenants(self.request)
        if tenant_dict and lbredundances:
            for lbr in lbredundances:
                tenant = tenant_dict.get(lbr.tenant_id, None)
                lbr.tenant_name = getattr(tenant, 'name', None)
        return lbredundances


class LoadbalancerDetailTabs(tabs.TabGroup):
    slug = "loadbalancer_details"
    tabs = (LoadbalancerOverviewTab,
            LbRedundancesTab)
    sticky = True


class AclsTab(tabs.TableTab):
    table_classes = (l_tables.AclsTable,)
    name = _("ACLs")
    slug = "acls_tab"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_acls_data(self):
        listener_id = self.tab_group.kwargs['listener_id']
        try:
            acls = api.lbaas_v2.acl_list(self.request,
                                         listener_id=listener_id)
        except Exception:
            acls = []
            exceptions.handle(self.request,
                              _('Unable to retrieve acl list.'))
        tenant_dict = utils.get_tenants(self.request)
        if tenant_dict and acls:
            for acl in acls:
                tenant = tenant_dict.get(acl.tenant_id, None)
                acl.tenant_name = getattr(tenant, 'name', None)
        return acls


class ListenerOverviewTab(tabs.Tab):
    name = _("Listener Overview")
    slug = "listeneroverview"
    template_name = "manager/loadbalancers/_listener_details.html"

    def get_context_data(self, request):
        return {"listener": self.tab_group.kwargs['listener']}


class ListenerDetailTabs(tabs.TabGroup):
    slug = "listener_details"
    tabs = (ListenerOverviewTab, AclsTab,)
    sticky = True


class MembersTab(tabs.TableTab):
    table_classes = (l_tables.MembersTable,)
    name = _("Members")
    slug = "members_tab"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_members_data(self):
        pool_id = self.tab_group.kwargs['pool_id']
        try:
            members = api.lbaas_v2.member_list(self.request,
                                               pool=pool_id,
                                               pool_id=pool_id)
            tenant_dict = utils.get_tenants(self.request)
            for m in members:
                m.pool_id = pool_id
                tenant = tenant_dict.get(m.tenant_id, None)
                m.tenant_name = getattr(tenant, 'name', None)
        except Exception:
            members = []
            exceptions.handle(self.request,
                              _('Unable to retrieve member list.'))
        return members


class PoolOverviewTab(tabs.Tab):
    name = _("Pool Overview")
    slug = "pooloverview"
    template_name = "manager/loadbalancers/_pool_details.html"

    def get_context_data(self, request):
        return {"pool": self.tab_group.kwargs['pool']}


class PoolDetailTabs(tabs.TabGroup):
    slug = "member_details"
    tabs = (PoolOverviewTab, MembersTab,)
    sticky = True
