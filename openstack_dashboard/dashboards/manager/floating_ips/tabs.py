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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "manager/floating_ips/_detail_overview.html"

    def get_context_data(self, request):
        floating_ip_id = self.tab_group.kwargs['floating_ip_id']
        try:
            floating_ip = api.network.tenant_floating_ip_get(
                self.request,
                floating_ip_id)
        except Exception:
            msg = _('Can not get floating IP detail.')
            url = reverse('horizon:manager:floating_ips:index')
            exceptions.handle(self.request, msg, redirect=url)
        return {'floating_ip': floating_ip}


class FloatingIPDetailTabs(tabs.TabGroup):
    slug = "floatingip_details"
    tabs = (OverviewTab,)
