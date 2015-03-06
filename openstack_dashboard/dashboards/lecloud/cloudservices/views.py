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
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.lecloud.cloudservices \
    import forms as project_forms
from openstack_dashboard.dashboards.lecloud.cloudservices \
    import tables as project_tables
from openstack_dashboard.dashboards.lecloud.cloudservices \
    import tabs as project_tabs

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.CloudServicesTable
    template_name = 'lecloud/cloudservices/index.html'

    def get_data(self):
        try:
            cloudservices = api.azure_api.cloud_service_list(self.request)
        except Exception:
            cloudservices = []
            exceptions.handle(self.request,
                              _('Unable to retrieve cloud service list.'))
        return cloudservices


class CreateCloudServiceView(forms.ModalFormView):
    form_class = project_forms.CreateCloudServiceForm
    template_name = 'lecloud/cloudservices/create_cloudservice.html'
    success_url = reverse_lazy('horizon:lecloud:cloudservices:index')

    def get_initial(self):
        initial = super(CreateCloudServiceView, self).get_initial()
        try:
            locations = api.azure_api.location_list(self.request)
        except Exception:
            locations = []
            redirect = reverse("horizon:lecloud:cloudservices:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve location list.'),
                              redirect=redirect)
        initial['locations'] = locations

        return initial


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.CloudServiceTabs
    template_name = 'lecloud/cloudservices/detail.html'
    redirect_url = 'horizon:lecloud:cloudservices:index'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        cloudservice = self.get_data()
        context["cloudservice"] = cloudservice
        table = project_tables.CloudServicesTable(self.request)
        context["url"] = reverse(self.redirect_url)
        context["actions"] = table.render_row_actions(cloudservice)
        context["page_title"] = _(
            "Cloud Service Details: %(service_name)s") % {
                'service_name': cloudservice.service_name}
        return context

    @memoized.memoized_method
    def get_data(self):
        cloud_service_name = self.kwargs['cloud_service_name']
        try:
            cloudservice = api.azure_api.cloud_service_detail(
                self.request,
                cloud_service_name)
        except Exception:
            cloudservice = None
            redirect = reverse("horizon:lecloud:cloudservices:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve cloud service detail.'),
                              redirect=redirect)
        return cloudservice

    def get_tabs(self, request, *args, **kwargs):
        cloudservice = self.get_data()
        return self.tab_group_class(request,
                                    cloudservice=cloudservice,
                                    **kwargs)
