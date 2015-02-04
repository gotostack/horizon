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

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard.dashboards.azure.instances \
    import tables as az_table


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("azure/instances/"
                     "_detail_overview.html")

    def get_context_data(self, request):
        return {"instance": self.tab_group.kwargs['instance']}


class EndpointTab(tabs.TableTab):
    table_classes = (az_table.EndpointsTable,)
    name = _("Instance Endpoints")
    slug = "instance_endpoints"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_instance_endpoints_data(self):
        instance = self.tab_group.kwargs['instance']
        endpoints = []
        for conf in instance.configuration_sets:
            if getattr(conf, 'input_endpoints') is not None:
                endpoints += conf.input_endpoints
        return endpoints


class InstanceDetailTabs(tabs.TabGroup):
    slug = "instance_details"
    tabs = (OverviewTab, EndpointTab)
    sticky = True
