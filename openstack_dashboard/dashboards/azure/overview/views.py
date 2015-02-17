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


class WelcomeTab(tabs.Tab):
    name = _("Quick Start")
    slug = "quickstart"
    template_name = "azure/overview/quickstart.html"


class InstanceTab(tabs.Tab):
    name = _("Instance")
    slug = "instance"
    template_name = "azure/overview/instance.html"


class CloudServiceTab(tabs.Tab):
    name = _("Cloud Service")
    slug = "cloudservice"
    template_name = "azure/overview/cloudservice.html"


class DiskTab(tabs.Tab):
    name = _("Disk")
    slug = "disk"
    template_name = "azure/overview/disk.html"


class WelcomeTabs(tabs.TabGroup):
    slug = "welcome_tabs"
    tabs = (WelcomeTab, InstanceTab, CloudServiceTab, DiskTab)


class WelcomeView(tabs.TabView):
    tab_group_class = WelcomeTabs
    template_name = 'azure/overview/index.html'