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
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.azure.instances \
    import forms as project_forms
from openstack_dashboard.dashboards.azure.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.azure.instances \
    import tabs as project_tabs
from openstack_dashboard.dashboards.azure.instances \
    import workflows as project_workflows

LOG = logging.getLogger(__name__)


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
                        role_dict = dict([(r.role_name, r)
                                          for r in dep.role_list])
                        for ins in dep.role_instance_list:
                            # set cloud service name
                            ins.cloud_service_name = cs.service_name
                            # set deployment name
                            ins.deployment_name = dep.name
                            ins.role = role_dict.get(ins.role_name)
                            ins.role_size = rolesize_dict.get(
                                ins.role.role_size)
                            instances.append(ins)
                except Exception:
                    exceptions.handle(
                        self.request,
                        _('Unable to retrieve cloud service detail.'))

        return instances


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.InstanceDetailTabs
    template_name = 'azure/instances/detail.html'
    redirect_url = 'horizon:azure:instances:index'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        instance = self.get_data()
        context["instance"] = instance
        context["url"] = reverse(self.redirect_url)
        context["page_title"] = _(
            "Instance Details: %(instance_name)s") % {
                'instance_name': instance.role_name}
        return context

    @memoized.memoized_method
    def get_data(self):
        cloud_service_name = self.kwargs['cloud_service_name']
        deployment_name = self.kwargs['deployment_name']
        instance_name = self.kwargs['instance_name']
        try:
            instance = api.azure_api.virtual_machine_get(
                self.request,
                cloud_service_name,
                deployment_name,
                instance_name)
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'instance "%s".') % instance_name,
                              redirect=redirect)
            # Not all exception types handled above will result in a redirect.
            # Need to raise here just in case.
            raise exceptions.Http302(redirect)

        if instance:
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
        project = next((proj for proj in self.request.user.authorized_tenants
                        if proj.id == self.request.user.project_id), None)
        if project:
            initial['subscription_id'] = project.subscription_id

        return initial


class UpdateView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateInstance
    success_url = reverse_lazy("horizon:azure:instances:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["cloud_service_name"] = self.kwargs['cloud_service_name']
        context["deployment_name"] = self.kwargs['deployment_name']
        context["instance_name"] = self.kwargs['instance_name']
        return context

    @memoized.memoized_method
    def get_flavors(self, *args, **kwargs):
        try:
            # To retrieve all vm size
            return api.azure_api.role_size_list(self.request)
        except Exception:
            redirect = reverse("horizon:azure:instances:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve azure role size list.'),
                              redirect=redirect)

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        cloud_service_name = self.kwargs['cloud_service_name']
        deployment_name = self.kwargs['deployment_name']
        instance_name = self.kwargs['instance_name']
        try:
            instance = api.azure_api.virtual_machine_get(
                self.request,
                cloud_service_name,
                deployment_name,
                instance_name)
            instance.cloud_service_name = cloud_service_name
            instance.deployment_name = deployment_name
            flavors = self.get_flavors()
            flavors_dict = dict([(item.name, item) for item in flavors])
            instance.role = flavors_dict.get(instance.role_size)
        except Exception:
            redirect = reverse("horizon:azure:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)
        return instance

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update(
                {'cloud_service_name': self.kwargs['cloud_service_name'],
                 'deployment_name': self.kwargs['deployment_name'],
                 'name': self.kwargs['instance_name'],
                 'availability_set_name': getattr(_object,
                                                  'availability_set_name',
                                                  '')})
        return initial


class ResizeView(UpdateView):
    workflow_class = project_workflows.ResizeInstance

    def get_initial(self):
        initial = super(ResizeView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update(
                {'cloud_service_name': self.kwargs['cloud_service_name'],
                 'deployment_name': self.kwargs['deployment_name'],
                 'name': self.kwargs['instance_name'],
                 'old_flavor_id': getattr(_object, 'role_size', ''),
                 'old_flavor_name': _object.role.label,
                 'flavors': self.get_flavors()})
        return initial


class AddEndpointView(forms.ModalFormView):
    form_class = project_forms.AddEndpointForm
    template_name = 'azure/instances/add_endpoint.html'
    success_url = reverse_lazy('horizon:azure:instances:index')

    def get_context_data(self, **kwargs):
        context = super(AddEndpointView, self).get_context_data(**kwargs)
        context["cloud_service_name"] = self.kwargs['cloud_service_name']
        context["deployment_name"] = self.kwargs['deployment_name']
        context["instance_name"] = self.kwargs['instance_name']
        return context

    def get_initial(self):
        return {'cloud_service_name': self.kwargs['cloud_service_name'],
                'deployment_name': self.kwargs['deployment_name'],
                'instance_name': self.kwargs['instance_name']}


class RemoveEndpointView(AddEndpointView):
    form_class = project_forms.RemoveEndpointForm
    template_name = 'azure/instances/remove_endpoint.html'

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        cloud_service_name = self.kwargs['cloud_service_name']
        deployment_name = self.kwargs['deployment_name']
        instance_name = self.kwargs['instance_name']
        try:
            instance = api.azure_api.virtual_machine_get(
                self.request,
                cloud_service_name,
                deployment_name,
                instance_name)
            instance.cloud_service_name = cloud_service_name
            instance.deployment_name = deployment_name
        except Exception:
            redirect = reverse("horizon:azure:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)
        return instance

    def get_initial(self):
        initial = super(RemoveEndpointView, self).get_initial()
        _object = self.get_object()
        if _object:
            network_config = None
            for cf in _object.configuration_sets:
                network_config = cf if (cf.configuration_set_type ==
                                        'NetworkConfiguration') else None
            if network_config and network_config.input_endpoints is not None:
                endpoints = network_config.input_endpoints.input_endpoints
            else:
                endpoints = []
            initial.update(
                {'cloud_service_name': self.kwargs['cloud_service_name'],
                 'deployment_name': self.kwargs['deployment_name'],
                 'instance_name': self.kwargs['instance_name'],
                 'endpoints': endpoints})
        return initial


class AttachDataDiskView(AddEndpointView):
    form_class = project_forms.AttatchDatadiskForm
    template_name = 'azure/instances/attach_datadisk.html'

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        try:
            disks = api.azure_api.disk_list(self.request)
        except Exception:
            disks = []
            redirect = reverse("horizon:azure:instances:index")
            msg = _('Unable to retrieve disk list.')
            exceptions.handle(self.request, msg, redirect=redirect)
        return disks

    def get_initial(self):
        initial = super(AttachDataDiskView, self).get_initial()
        disks = self.get_object()
        if disks:
            initial.update(
                {'cloud_service_name': self.kwargs['cloud_service_name'],
                 'deployment_name': self.kwargs['deployment_name'],
                 'instance_name': self.kwargs['instance_name'],
                 'data_disks': [d for d in disks if d.attached_to is None]})
        return initial


class DeattachDataDiskView(AddEndpointView):
    form_class = project_forms.DeattatchDatadiskForm
    template_name = 'azure/instances/deattach_datadisk.html'

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        cloud_service_name = self.kwargs['cloud_service_name']
        deployment_name = self.kwargs['deployment_name']
        instance_name = self.kwargs['instance_name']
        try:
            instance = api.azure_api.virtual_machine_get(
                self.request,
                cloud_service_name,
                deployment_name,
                instance_name)
            instance.cloud_service_name = cloud_service_name
            instance.deployment_name = deployment_name
        except Exception:
            redirect = reverse("horizon:azure:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)
        return instance

    def get_initial(self):
        initial = super(DeattachDataDiskView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update(
                {'cloud_service_name': self.kwargs['cloud_service_name'],
                 'deployment_name': self.kwargs['deployment_name'],
                 'instance_name': self.kwargs['instance_name'],
                 'data_disks': _object.data_virtual_hard_disks})
        return initial
