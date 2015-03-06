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

import logging


from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.lecloud.disks \
    import tables as project_tables
from openstack_dashboard.dashboards.lecloud.disks \
    import tabs as project_tabs

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.DisksTable
    template_name = 'lecloud/disks/index.html'

    def get_data(self):
        try:
            disks = api.azure_api.disk_list(self.request)
        except Exception:
            disks = []
            exceptions.handle(self.request,
                              _('Unable to retrieve disk list.'))
        return disks


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.DiskTabs
    template_name = 'lecloud/disks/detail.html'
    redirect_url = 'horizon:lecloud:disks:index'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        disk = self.get_data()
        context["disk"] = disk
        table = project_tables.DisksTable(self.request)
        context["url"] = reverse(self.redirect_url)
        context["actions"] = table.render_row_actions(disk)
        context["page_title"] = _(
            "Disk Details: %(name)s") % {
                'name': disk.name}
        return context

    @memoized.memoized_method
    def get_data(self):
        disk_name = self.kwargs['disk_name']
        try:
            disk = api.azure_api.disk_get(self.request, disk_name)
        except Exception:
            disk = None
            redirect = reverse("horizon:lecloud:disks:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve disk detail.'),
                              redirect=redirect)
        return disk

    def get_tabs(self, request, *args, **kwargs):
        disk = self.get_data()
        return self.tab_group_class(request, disk=disk, **kwargs)
