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
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.floating_ips \
    import forms as fip_forms
from openstack_dashboard.dashboards.admin.floating_ips \
    import tables as fip_tables
from openstack_dashboard.dashboards.admin.floating_ips \
    import tabs as fip_tabs


class IndexView(tables.DataTableView):
    table_class = fip_tables.FloatingIPsTable
    template_name = 'admin/floating_ips/index.html'

    @memoized.memoized_method
    def get_data(self):
        floating_ips = []
        try:
            floating_ips = api.network.tenant_floating_ip_list(
                self.request,
                all_tenants=True)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP list.'))

        if floating_ips:
            instances = []
            try:
                instances, has_more = api.nova.server_list(self.request,
                                                           all_tenants=True)
            except Exception:
                exceptions.handle(
                    self.request,
                    _('Unable to retrieve instance list.'))
            instances_dict = dict([(obj.id, obj.name) for obj in instances])

            tenants = []
            try:
                tenants, has_more = api.keystone.tenant_list(self.request)
            except Exception:
                msg = _('Unable to retrieve project list.')
                exceptions.handle(self.request, msg)
            tenant_dict = SortedDict([(t.id, t) for t in tenants])

            networks = []
            try:
                params = {"router:external": True}
                networks = api.neutron.network_list(self.request,
                                                    **params)
            except Exception:
                msg = _('Unable to retrieve network list.')
                exceptions.handle(self.request, msg)
            network_dict = dict([(obj.id, obj.name) for obj in networks])

            for ip in floating_ips:
                ip.instance_name = instances_dict.get(ip.instance_id)
                ip.floating_network = network_dict.get(ip.floating_network_id,
                                                       ip.floating_network_id)
                tenant = tenant_dict.get(ip.tenant_id, None)
                ip.tenant_name = getattr(tenant, "name", None)

        return floating_ips


class DetailView(tabs.TabView):
    tab_group_class = fip_tabs.FloatingIPDetailTabs
    template_name = 'admin/floating_ips/detail.html'


class AllocateView(forms.ModalFormView):
    form_class = fip_forms.AdminFloatingIpAllocate
    template_name = 'admin/floating_ips/allocate.html'
    success_url = reverse_lazy('horizon:admin:floating_ips:index')

    @memoized.memoized_method
    def get_initial(self):
        tenants = []
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            msg = _('Unable to retrieve project list.')
            exceptions.handle(self.request, msg)
        tenant_list = [(t.id, t.name) for t in tenants]
        if not tenant_list:
            tenant_list = [(None, _("No project available"))]

        try:
            pools = api.network.floating_ip_pools_list(self.request)
        except Exception:
            pools = []
            exceptions.handle(self.request,
                              _("Unable to retrieve floating IP pools."))
        pool_list = [(pool.id, pool.name) for pool in pools]
        if not pool_list:
            pool_list = [(None, _("No floating IP pools available"))]

        return {'pool_list': pool_list,
                'tenant_list': tenant_list}
