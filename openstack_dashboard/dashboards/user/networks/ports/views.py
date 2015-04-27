# Copyright 2012 NEC Corporation
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
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.user.networks.ports \
    import forms as user_forms
from openstack_dashboard.dashboards.user.networks.ports \
    import tables as user_tables
from openstack_dashboard.dashboards.user.networks.ports \
    import tabs as user_tabs

STATE_DICT = dict(user_tables.DISPLAY_CHOICES)
STATUS_DICT = dict(user_tables.STATUS_DISPLAY_CHOICES)


class DetailView(tabs.TabView):
    tab_group_class = user_tabs.PortDetailTabs
    template_name = 'user/networks/ports/detail.html'
    page_title = _("Port Details")

    @memoized.memoized_method
    def get_data(self):
        port_id = self.kwargs['port_id']

        try:
            port = api.neutron.port_get(self.request, port_id)
            port.admin_state_label = STATE_DICT.get(port.admin_state,
                                                    port.admin_state)
            port.status_label = STATUS_DICT.get(port.status,
                                                port.status)
        except Exception:
            port = []
            redirect = self.get_redirect_url()
            msg = _('Unable to retrieve port details.')
            exceptions.handle(self.request, msg, redirect=redirect)

        if (api.neutron.is_extension_supported(self.request, 'mac-learning')
                and not hasattr(port, 'mac_state')):
            port.mac_state = api.neutron.OFF_STATE

        return port

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        port = self.get_data()
        table = user_tables.PortsTable(self.request,
                                       network_id=port.network_id)
        context["port"] = port
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(port)
        return context

    def get_tabs(self, request, *args, **kwargs):
        port = self.get_data()
        return self.tab_group_class(request, port=port, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:user:networks:index')


class UpdateView(forms.ModalFormView):
    form_class = user_forms.UpdatePort
    form_id = "update_port_form"
    modal_header = _("Edit Port")
    template_name = 'user/networks/ports/update.html'
    context_object_name = 'port'
    submit_label = _("Save Changes")
    submit_url = "horizon:user:networks:editport"
    success_url = 'horizon:user:networks:detail'
    page_title = _("Update Port")

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['network_id'],))

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        port_id = self.kwargs['port_id']
        try:
            return api.neutron.port_get(self.request, port_id)
        except Exception:
            redirect = self.get_success_url()
            msg = _('Unable to retrieve port details')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        port = self._get_object()
        context['port_id'] = port['id']
        context['network_id'] = port['network_id']
        args = (self.kwargs['network_id'], self.kwargs['port_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        port = self._get_object()
        initial = {'port_id': port['id'],
                   'network_id': port['network_id'],
                   'tenant_id': port['tenant_id'],
                   'name': port['name'],
                   'admin_state': port['admin_state_up']}
        if port['binding__vnic_type']:
            initial['binding__vnic_type'] = port['binding__vnic_type']
        try:
            initial['mac_state'] = port['mac_learning_enabled']
        except Exception:
            # MAC Learning is not set
            pass
        return initial