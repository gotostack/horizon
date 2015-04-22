# Copyright 2015 Letv Cloud Computing
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

from django.utils.translation import ugettext_lazy as _

from horizon import tabs


class WelcomeTab(tabs.Tab):
    name = _("Welcome")
    slug = "welcome"
    template_name = "user/welcome/detail.html"

    def get_context_data(self, request):
        return {}


class WelcomeTabs(tabs.TabGroup):
    slug = "welcome_tabs"
    tabs = (WelcomeTab,)


class WelcomeView(tabs.TabView):
    tab_group_class = WelcomeTabs
    template_name = 'user/welcome/index.html'
