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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


def get_tenant_network_resources_quotas(request, tenant_id):
    try:
        quotas = api.neutron.tenant_quota_get(request, tenant_id)
        limit = {}
        for q in quotas:
            if q.limit == -1:
                limit[q.name] = float("inf")
            else:
                limit[q.name] = int(q.limit)
        return limit
    except Exception:
        pass


def get_tenant_network_resources_usages(request, tenant_id):
    usages = {}
    floating_ips = []
    try:
        if api.network.floating_ip_supported(request):
            floating_ips = api.network.tenant_floating_ip_list(request)
    except Exception:
        pass
    usages['floating_ip'] = len(floating_ips)

    security_groups = []
    try:
        security_groups = api.network.security_group_list(request)
    except Exception:
        pass
    usages['security_group'] = len(security_groups)

    networks = []
    try:
        networks = api.neutron.network_list(request)
        if tenant_id:
            networks = filter(lambda net: net.tenant_id == tenant_id, networks)
    except Exception:
        pass
    usages['network'] = len(networks)

    subnets = []
    try:
        subnets = api.neutron.subnet_list(request)
    except Exception:
        pass
    usages['subnet'] = len(subnets)

    routers = []
    try:
        routers = api.neutron.router_list(request)
        if tenant_id:
            routers = filter(lambda rou: rou.tenant_id == tenant_id, routers)
    except Exception:
        pass
    usages['router'] = len(routers)

    acls = []
    try:
        acls = api.lbaas_v2.acl_list(request)
        if tenant_id:
            acls = filter(lambda acl: acl.tenant_id == tenant_id, acls)
    except Exception:
        pass
    usages['acl'] = len(acls)

    loadbalancers = []
    try:
        loadbalancers = api.lbaas_v2.loadbalancer_list(request)
        if tenant_id:
            loadbalancers = filter(lambda lb: lb.tenant_id == tenant_id,
                                   loadbalancers)
    except Exception:
        pass
    usages['loadbalancer'] = len(loadbalancers)

    return usages


class LoadbalancerTable(tables.DataTable):
    loadbalancer = tables.Column('name',
                                 verbose_name=_("Name"))
    vip_address = tables.Column('vip_address',
                                verbose_name=_("IP Address"))

    def get_object_id(self, datum):
        return datum.get('id', id(datum))

    class Meta(object):
        name = "project_usage"
        hidden_title = False
        verbose_name = _("Loadbalancer Overview")
        columns = ("loadbalancer", "vip_address")
        multi_select = False


class ProjectOverview(tables.DataTableView):
    table_class = LoadbalancerTable
    template_name = 'user/overview/index.html'

    def get_context_data(self, **kwargs):
        context = super(ProjectOverview, self).get_context_data(**kwargs)
        context['usage'] = self.get_usage()
        return context

    def get_usage(self):
        tenant_id = self.request.user.tenant_id
        usg = {}
        try:
            usg["used"] = get_tenant_network_resources_usages(
                self.request, tenant_id=tenant_id)
            usg["limit"] = get_tenant_network_resources_quotas(
                self.request, tenant_id=tenant_id)
        except Exception:
            usg = None
            msg = _('Unable to retrieve tenant quota usage.')
            exceptions.handle(self.request, msg)
        return usg

    def get_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            loadbalancers = api.lbaas_v2.loadbalancer_list(
                self.request, tenant_id=tenant_id)
        except Exception:
            loadbalancers = []
            msg = _('Unable to retrieve loadbalancer list.')
            exceptions.handle(self.request, msg)
        return loadbalancers
