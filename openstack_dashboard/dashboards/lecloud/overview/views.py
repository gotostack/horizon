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

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api


class WelcomeTab(tabs.Tab):
    name = _("Quick Start")
    slug = "quickstart"
    template_name = "lecloud/overview/quickstart.html"

    def get_context_data(self, request, **kwargs):
        context = super(WelcomeTab, self).get_context_data(request, **kwargs)
        try:
            self.usage = api.azure_api.subscription_get(request)
            project = next((proj for proj in request.user.authorized_tenants
                            if proj.id == request.user.project_id), None)
            if (getattr(project, "max_hosted_services", None)
                    and getattr(project, "max_core_count", None)):
                self.usage.max_hosted_services = project.max_hosted_services
                self.usage.max_core_count = project.max_core_count
        except Exception:
            self.usage = None
            exceptions.handle(self.request,
                              _('Unable to get subscription info.'))
        context['usage'] = self.usage
        return context


class InstanceTab(tabs.Tab):
    name = _("Instance")
    slug = "instance"
    template_name = "lecloud/overview/instance.html"


class CloudServiceTab(tabs.Tab):
    name = _("Cloud Service")
    slug = "cloudservice"
    template_name = "lecloud/overview/cloudservice.html"


class DiskTab(tabs.Tab):
    name = _("Disk")
    slug = "disk"
    template_name = "lecloud/overview/disk.html"


class WelcomeTabs(tabs.TabGroup):
    slug = "welcome_tabs"
    tabs = (WelcomeTab, InstanceTab, CloudServiceTab, DiskTab)


class WelcomeView(tabs.TabView):
    tab_group_class = WelcomeTabs
    template_name = 'lecloud/overview/index.html'
    redirect_url = 'horizon:lecloud:overview:index'
    page_title = _("Welcome")
