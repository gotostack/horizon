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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.manager.lbaas_v2_agents \
    import tables as lbagent_tables
from openstack_dashboard.dashboards.manager.loadbalancers \
    import tables as lb_tables
from openstack_dashboard.dashboards.manager.loadbalancers \
    import utils as lb_utils


class IndexView(tables.DataTableView):
    table_class = lbagent_tables.LbaasV2AgentsTable
    template_name = 'manager/lbaas_v2_agents/index.html'
    page_title = _("Load Balancing v2 Agents")

    @memoized.memoized_method
    def get_data(self):
        lbaas_v2_agents = []
        try:
            agents = api.neutron.agent_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve agent list.'))
            agents = []

        for a in agents:
            if a.agent_type == "Loadbalancerv2 agent":
                lbaas_v2_agents.append(a)

        return lbaas_v2_agents


class DetailView(tables.MultiTableView):
    table_classes = (lb_tables.LoadbalancerTable,)
    template_name = 'manager/lbaas_v2_agents/detail.html'
    page_title = _("Load Balancing v2 Agent Details")

    def get_loadbalancers_data(self):
        subnet_dict = dict([(
            n.id, n.cidr) for n in lb_utils.get_subnets(self.request)])
        tenant_dict = lb_utils.get_tenants(self.request)
        try:
            agent_id = self.kwargs['agent_id']
            loadbalancers = api.lbaas_v2.get_loadbalancer_list_on_agent(
                self.request, agent_id)
        except Exception:
            loadbalancers = []
            msg = _('Unable to list the loadbalancers'
                    ' on a loadbalancer v2 agent: %s.') % agent_id
            exceptions.handle(self.request, msg)

        if subnet_dict and tenant_dict and loadbalancers:
                for lb in loadbalancers:
                    lb.subnet_name = subnet_dict.get(lb.vip_subnet_id)
                    tenant = tenant_dict.get(lb.tenant_id, None)
                    lb.tenant_name = getattr(tenant, 'name', None)
        return loadbalancers

    @memoized.memoized_method
    def _get_data(self):
        try:
            agent_id = self.kwargs['agent_id']
            agent = api.neutron.agent_get(self.request, agent_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'agent "%s".') % agent_id,
                              redirect=self.get_redirect_url())

        return agent

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["agent"] = self._get_data()
        return context

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:manager:lbaas_v2_agents:index')
