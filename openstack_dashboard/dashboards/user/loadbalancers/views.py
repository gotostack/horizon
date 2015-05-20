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
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.user.loadbalancers \
    import forms as user_forms
from openstack_dashboard.dashboards.user.loadbalancers \
    import tabs as user_tabs
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
    page_title = _("Loadbalancer Details: {{ loadbalancer.name }}")

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

    def _get_stats(self):
        try:
            loadbalancer_id = self.kwargs['loadbalancer_id']
            stats = api.lbaas_v2.loadbalancer_stats(self.request,
                                                    loadbalancer_id)
        except Exception:
            msg = _('Unable to retrieve stats for loadbalancer "%s".') \
                % loadbalancer_id
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        return stats

    def get_context_data(self, **kwargs):
        context = super(LoadbalancerDetailView,
                        self).get_context_data(**kwargs)
        loadbalancer = self._get_data()
        loadbalancer.stats = self._get_stats()
        context["loadbalancer"] = loadbalancer
        context["loadbalancer_id"] = loadbalancer.id
        return context

    def get_tabs(self, request, *args, **kwargs):
        loadbalancer = self._get_data()
        return self.tab_group_class(request,
                                    loadbalancer=loadbalancer,
                                    **kwargs)


class LoadbalancerStatusesDetailView(forms.ModalFormMixin,
                                     generic.TemplateView):
    template_name = 'user/loadbalancers/loadbalancer_statuses.html'
    page_title = _("Loadbalancer Statuses")

    @memoized.memoized_method
    def get_object(self):
        try:
            loadbalancer_id = self.kwargs['loadbalancer_id']
            return api.lbaas_v2.loadbalancer_statuses(self.request,
                                                      loadbalancer_id)
        except Exception:
            redirect = reverse("horizon:user:loadbalancers:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve loadbalancers statuses.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(LoadbalancerStatusesDetailView,
                        self).get_context_data(**kwargs)
        context['statuses'] = self.get_object()
        return context


class ListenerDetailsView(tabs.TabbedTableView):
    tab_group_class = user_tabs.ListenerDetailTabs
    template_name = 'user/loadbalancers/listener_detail.html'
    failure_url = reverse_lazy('horizon:user:loadbalancers:index')
    page_title = _("Listener Details: {{ listener.name }}")

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
    page_title = _("Pool Details: {{ pool.name }}")

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


class AddLoadbalancerView(workflows.WorkflowView):
    workflow_class = user_workflows.AddLoadbalancer


class UpdateLoadbalancerView(forms.ModalFormView):
    form_class = user_forms.UpdateLoadbalancer
    form_id = "update_loadbalancer_form"
    modal_header = _("Edit Loadbalancer")
    template_name = "user/loadbalancers/updateloadbalancer.html"
    context_object_name = 'loadbalancer'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updateloadbalancer"
    success_url = reverse_lazy("horizon:user:loadbalancers:index")
    page_title = _("Edit Loadbalancer")

    def get_context_data(self, **kwargs):
        context = super(UpdateLoadbalancerView,
                        self).get_context_data(**kwargs)
        context["loadbalancer_id"] = self.kwargs['loadbalancer_id']
        args = (self.kwargs['loadbalancer_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        loadbalancer_id = self.kwargs['loadbalancer_id']
        try:
            return api.lbaas_v2.loadbalancer_get(self.request,
                                                 loadbalancer_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve loadbalancer details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        lb = self._get_object()
        return {'id': lb['id'],
                'name': lb['name'],
                'description': lb['description'],
                'admin_state_up': lb['admin_state_up']}


class AddListenerView(workflows.WorkflowView):
    workflow_class = user_workflows.AddListener


class UpdateListenerView(forms.ModalFormView):
    form_class = user_forms.UpdateListener
    form_id = "update_listener_form"
    modal_header = _("Edit Listener")
    template_name = "user/loadbalancers/updatelistener.html"
    context_object_name = 'listener'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updatelistener"
    success_url = reverse_lazy("horizon:user:loadbalancers:index")
    page_title = _("Edit Listener")

    def get_context_data(self, **kwargs):
        context = super(UpdateListenerView,
                        self).get_context_data(**kwargs)
        context["listener_id"] = self.kwargs['listener_id']
        args = (self.kwargs['listener_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        listener_id = self.kwargs['listener_id']
        try:
            return api.lbaas_v2.listener_get(self.request,
                                             listener_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve listener details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obj = self._get_object()
        return {'id': _obj['id'],
                'name': _obj['name'],
                'description': _obj['description'],
                'admin_state_up': _obj['admin_state_up']}


class AddPoolView(workflows.WorkflowView):
    workflow_class = user_workflows.AddPool


class UpdatePoolView(forms.ModalFormView):
    form_class = user_forms.UpdatePool
    form_id = "update_pool_form"
    modal_header = _("Edit Pool")
    template_name = "user/loadbalancers/updatepool.html"
    context_object_name = 'pool'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updatepool"
    success_url = reverse_lazy("horizon:user:loadbalancers:index")
    page_title = _("Edit Pool")

    def get_context_data(self, **kwargs):
        context = super(UpdatePoolView,
                        self).get_context_data(**kwargs)
        context["pool_id"] = self.kwargs['pool_id']
        args = (self.kwargs['pool_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        pool_id = self.kwargs['pool_id']
        try:
            return api.lbaas_v2.pool_get(self.request,
                                         pool_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve pool details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obg = self._get_object()
        return {'id': _obg['id'],
                'name': _obg['name'],
                'description': _obg['description'],
                'admin_state_up': _obg['admin_state_up'],
                'lb_algorithm': _obg['lb_algorithm']}


class AddMemberView(workflows.WorkflowView):
    workflow_class = user_workflows.AddMember

    def get_initial(self):
        return {"pool_id": self.kwargs['pool_id']}


class UpdateMemberView(forms.ModalFormView):
    form_class = user_forms.UpdateMember
    form_id = "update_member_form"
    modal_header = _("Edit Member")
    template_name = "user/loadbalancers/updatemember.html"
    context_object_name = 'member'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updatemember"
    success_url = "horizon:user:loadbalancers:pooldetails"
    page_title = _("Edit Member")

    def get_context_data(self, **kwargs):
        context = super(UpdateMemberView,
                        self).get_context_data(**kwargs)
        context["pool_id"] = self.kwargs['pool_id']
        context["member_id"] = self.kwargs['member_id']
        args = (self.kwargs['pool_id'],
                self.kwargs['member_id'])
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['pool_id'],))

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        member_id = self.kwargs['member_id']
        pool_id = self.kwargs['pool_id']
        try:
            return api.lbaas_v2.member_get(self.request,
                                           member_id,
                                           pool_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve member details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obg = self._get_object()
        return {'member_id': _obg['id'],
                'pool_id': self.kwargs['pool_id'],
                'weight': _obg['weight'],
                'admin_state_up': _obg['admin_state_up'],
                'subnet_id': _obg['subnet_id']}


class AddAclView(workflows.WorkflowView):
    workflow_class = user_workflows.AddAcl

    def get_initial(self):
        return {"listener_id": self.kwargs['listener_id']}


class UpdateAclView(forms.ModalFormView):
    form_class = user_forms.UpdateAcl
    form_id = "update_acl_form"
    modal_header = _("Edit Acl")
    template_name = "user/loadbalancers/updateacl.html"
    context_object_name = 'acl'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updateacl"
    success_url = "horizon:user:loadbalancers:listenerdetails"
    page_title = _("Edit Acl")

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['listener_id'],))

    def get_context_data(self, **kwargs):
        context = super(UpdateAclView,
                        self).get_context_data(**kwargs)
        context["acl_id"] = self.kwargs['acl_id']
        context["listener_id"] = self.kwargs['listener_id']
        args = (self.kwargs['listener_id'],
                self.kwargs['acl_id'])
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        acl_id = self.kwargs['acl_id']
        try:
            return api.lbaas_v2.acl_get(self.request,
                                        acl_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve acl details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obg = self._get_object()
        return {'acl_id': _obg['id'],
                'listener_id': self.kwargs['listener_id'],
                'name': _obg['name'],
                'description': _obg['description'],
                'action': _obg['action'],
                'condition': _obg['condition'],
                'acl_type': _obg['acl_type'],
                'operator': _obg['operator'],
                'match': _obg['match'],
                'match_condition': _obg['match_condition'],
                'admin_state_up': _obg['admin_state_up']}


class AddHealthmonitorView(workflows.WorkflowView):
    workflow_class = user_workflows.AddHealthmonitor


class UpdateHealthmonitorView(forms.ModalFormView):
    form_class = user_forms.UpdateHealthmonitor
    form_id = "update_healthmonitor_form"
    modal_header = _("Edit Healthmonitor")
    template_name = "user/loadbalancers/updatehealthmonitor.html"
    context_object_name = 'healthmonitor'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updatehealthmonitor"
    success_url = reverse_lazy("horizon:user:loadbalancers:index")
    page_title = _("Edit Healthmonitor")

    def get_context_data(self, **kwargs):
        context = super(UpdateHealthmonitorView,
                        self).get_context_data(**kwargs)
        context["healthmonitor_id"] = self.kwargs['healthmonitor_id']
        args = (self.kwargs['healthmonitor_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        healthmonitor_id = self.kwargs['healthmonitor_id']
        try:
            return api.lbaas_v2.healthmonitor_get(self.request,
                                                  healthmonitor_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve healthmonitor details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obg = self._get_object()
        return {"healthmonitor_id": _obg["id"],
                "type": _obg["type"].lower(),
                "delay": _obg['delay'],
                "timeout": _obg['timeout'],
                "max_retries": _obg['max_retries'],
                "http_method": _obg['http_method'],
                "url_path": _obg['url_path'],
                "expected_codes": _obg['expected_codes'],
                "admin_state_up": _obg['admin_state_up']}


class AddRedundanceView(workflows.WorkflowView):
    workflow_class = user_workflows.AddRedundance

    def get_initial(self):
        return {"loadbalancer_id": self.kwargs['loadbalancer_id']}


class UpdateRedundanceView(forms.ModalFormView):
    form_class = user_forms.UpdateRedundance
    form_id = "update_redundance_form"
    modal_header = _("Edit Redundance")
    template_name = "user/loadbalancers/updateredundance.html"
    context_object_name = 'redundance'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updateredundance"
    success_url = "horizon:user:loadbalancers:loadbalancerdetails"
    page_title = _("Edit Redundance")

    def get_context_data(self, **kwargs):
        context = super(UpdateRedundanceView,
                        self).get_context_data(**kwargs)
        context["loadbalancer_id"] = self.kwargs['loadbalancer_id']
        context["redundance_id"] = self.kwargs['redundance_id']
        args = (self.kwargs['loadbalancer_id'],
                self.kwargs['redundance_id'])
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['loadbalancer_id'],))

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        redundance_id = self.kwargs['redundance_id']
        loadbalancer_id = self.kwargs['loadbalancer_id']
        try:
            return api.lbaas_v2.redundance_get(self.request,
                                               redundance_id,
                                               loadbalancer_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve redundance details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obg = self._get_object()
        return {'redundance_id': _obg['id'],
                'loadbalancer_id': self.kwargs['loadbalancer_id'],
                'name': _obg['name'],
                'description': _obg['description'],
                'admin_state_up': _obg['admin_state_up']}


class AddLVSPortView(workflows.WorkflowView):
    workflow_class = user_workflows.AddLVSPort


class UpdateLVSPortView(forms.ModalFormView):
    form_class = user_forms.UpdateLVSPort
    form_id = "update_lvsport_form"
    modal_header = _("Edit LVS Port")
    template_name = "user/loadbalancers/updatelvsport.html"
    context_object_name = 'lvsport'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:loadbalancers:updatelvsport"
    success_url = reverse_lazy("horizon:user:loadbalancers:index")
    page_title = _("Edit LVS Port")

    def get_context_data(self, **kwargs):
        context = super(UpdateLVSPortView,
                        self).get_context_data(**kwargs)
        context["lvs_id"] = self.kwargs['lvs_id']
        args = (self.kwargs['lvs_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        lvs_id = self.kwargs['lvs_id']
        try:
            return api.lbaas_v2.lvsport_get(self.request,
                                            lvs_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve lvs port details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        _obg = self._get_object()
        return {'lvs_id': _obg['id'],
                'name': _obg['name'],
                'description': _obg['description'],
                'admin_state_up': _obg['admin_state_up']}
