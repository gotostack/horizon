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

"""
Views for managing instances.
"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.azure.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.azure.instances \
    import tabs as project_tabs
from openstack_dashboard.dashboards.azure.instances \
    import workflows as project_workflows


class IndexView(tables.DataTableView):
    table_class = project_tables.InstancesTable
    template_name = 'azure/instances/index.html'

    def get_data(self):
        try:
            # To this subscription's all cloud service
            cloud_services = api.azure_api.cloud_service_list(self.request)
        except Exception:
            cloud_services = []
            exceptions.handle(self.request,
                              _('Unable to retrieve cloud service list.'))

        try:
            # To retrieve all vm size
            role_sizes = api.azure_api.role_size_list(self.request)
        except Exception:
            role_sizes = []
            exceptions.handle(self.request,
                              _('Unable to retrieve role size list.'))
        rolesize_dict = dict([(item.name, item) for item in role_sizes])

        instances = []
        if cloud_services and rolesize_dict:
            for cs in cloud_services:
                # To get all instances in each cloud service
                try:
                    detail = api.azure_api.cloud_service_detail(
                        self.request,
                        cs.service_name,
                        embed_detail=True)
                    for dep in detail.deployments:
                        for ins in dep.role_instance_list:
                            # set DNS
                            port = ':'
                            if ins.instance_endpoints:
                                endpoints = dict(
                                    [(p.name, p.public_port)
                                     for p in ins.instance_endpoints])
                                port += endpoints.get('SSH', "N/A")
                            ins.dns_url = dep.url[7:-1] + port
                            # set cloud service name
                            ins.cloud_service_name = cs.service_name
                            # set deployment name
                            ins.deployment_name = dep.name
                            instances.append(ins)
                except Exception:
                    exceptions.handle(
                        self.request,
                        _('Unable to retrieve cloud service detail.'))

        for ins in instances:
            # Set all instance its role(flavor)
            ins.role = rolesize_dict.get(ins.instance_size)
        return instances


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.InstanceDetailTabs
    template_name = 'azure/instances/detail.html'
    redirect_url = 'horizon:azure:instances:index'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        instance = self.get_data()
        context["instance"] = instance
        table = project_tables.InstancesTable(self.request)
        context["url"] = reverse(self.redirect_url)
        context["actions"] = table.render_row_actions(instance)
        context["page_title"] = _(
            "Instance Details: %(instance_name)s") % {
                'instance_name': instance.role_name}
        return context

    @memoized.memoized_method
    def get_data(self):
        cloud_service_name = self.kwargs['cloud_service_name']
        deployment_name = self.kwargs['deployment_name']
        instance_name = self.kwargs['instance_name']
        instance = api.azure_api.get_instance_detail(
            self.request,
            cloud_service_name,
            deployment_name,
            instance_name)
        instance.cloud_service_name = cloud_service_name
        instance.deployment_name = deployment_name
        return instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)


class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchInstance

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        tenant = api.keystone.tenant_get(self.request,
                                         self.request.user.tenant_id)
        initial['subscription_id'] = tenant.subscription_id

        return initial
