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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.user.loadbalancers \
    import forms as user_forms
from openstack_dashboard.dashboards.user.loadbalancers \
    import tables as user_tables
from openstack_dashboard.dashboards.user.loadbalancers \
    import tabs as user_tabs
from openstack_dashboard.dashboards.user.loadbalancers import utils
from openstack_dashboard.dashboards.user.loadbalancers \
    import workflows as user_workflows


class IndexView(tabs.TabbedTableView):
    tab_group_class = user_tabs.LoadbalancerTabs
    template_name = 'user/loadbalancers/index.html'
    page_title = _("Load Balancer")


class LoadbalancerDetailView(tabs.TabbedTableView):
    tab_group_class = user_tabs.LoadbalancerDetailTabs
    template_name = 'user/loadbalancers/loadbalancer_detail.html'
    failure_url = reverse_lazy('horizon:user:loadbalancers:index')
    page_title = _("Loadbalancer Details")

    @memoized.memoized_method
    def _get_data(self):
        try:
            loadbalancer_id = self.kwargs['loadbalancer_id']
            loadbalancer = api.lbaas_v2.loadbalancer_get(self.request,
                                                         loadbalancer_id)
        except Exception:
            msg = _('Unable to retrieve details for loadbalancer "%s".') \
                % loadbalancer_id
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        return loadbalancer

    def get_context_data(self, **kwargs):
        context = super(LoadbalancerDetailView,
                        self).get_context_data(**kwargs)
        loadbalancer = self._get_data()
        context["loadbalancer"] = loadbalancer
        return context

    def get_tabs(self, request, *args, **kwargs):
        loadbalancer = self._get_data()
        return self.tab_group_class(request,
                                    loadbalancer=loadbalancer,
                                    **kwargs)


class ListenerDetailsView(tabs.TabbedTableView):
    tab_group_class = user_tabs.ListenerDetailTabs
    template_name = 'user/loadbalancers/listener_detail.html'
    failure_url = reverse_lazy('horizon:user:loadbalancers:index')
    page_title = _("Listener Details")

    @memoized.memoized_method
    def _get_data(self):
        try:
            listener_id = self.kwargs['listener_id']
            listener = api.lbaas_v2.listener_get(self.request,
                                                 listener_id)
        except Exception:
            msg = _('Unable to retrieve details for listener "%s".') \
                % listener_id
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        return listener

    def get_context_data(self, **kwargs):
        context = super(ListenerDetailsView, self).get_context_data(**kwargs)
        listener = self._get_data()
        context["listener"] = listener
        context["listener_id"] = self.kwargs['listener_id']
        return context

    def get_tabs(self, request, *args, **kwargs):
        listener = self._get_data()
        return self.tab_group_class(request,
                                    listener=listener,
                                    **kwargs)


class PoolDetailsView(tabs.TabbedTableView):
    tab_group_class = user_tabs.PoolDetailTabs
    template_name = 'user/loadbalancers/pool_detail.html'
    failure_url = reverse_lazy('horizon:user:loadbalancers:index')
    page_title = _("Pool Details")

    @memoized.memoized_method
    def _get_data(self):
        try:
            pool_id = self.kwargs['pool_id']
            listener = api.lbaas_v2.pool_get(self.request,
                                             pool_id)
        except Exception:
            msg = _('Unable to retrieve details for pool "%s".') \
                % pool_id
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        return listener

    def get_context_data(self, **kwargs):
        context = super(PoolDetailsView, self).get_context_data(**kwargs)
        pool = self._get_data()
        context["pool"] = pool
        context["pool_id"] = self.kwargs['pool_id']
        return context

    def get_tabs(self, request, *args, **kwargs):
        pool = self._get_data()
        return self.tab_group_class(request,
                                    pool=pool,
                                    **kwargs)
