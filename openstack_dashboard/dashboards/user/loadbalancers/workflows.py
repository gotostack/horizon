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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.user.loadbalancers import utils


AVAILABLE_PROTOCOLS = ('TCP', 'HTTP', 'HTTPS', 'TERMINATED_HTTPS')
AVAILABLE_METHODS = ('ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP')


LOG = logging.getLogger(__name__)


class AddLoadbalancerAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    # provider is optional because some LBaaS implemetation does
    # not support service-type extension.
    provider = forms.ChoiceField(label=_("Provider"), required=False)

    vip_subnet_id = forms.ChoiceField(label=_("VIP Subnet"))
    vip_address = forms.IPField(label=_("Specify a free IP address "
                                    "from the selected subnet"),
                            version=forms.IPv4,
                            mask=False,
                            required=False)

    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddLoadbalancerAction, self).__init__(request, *args, **kwargs)
        tenant_id = request.user.tenant_id
        subnet_id_choices = [('', _("Select a Subnet"))]
        try:
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve networks list.'))
            networks = []
        for n in networks:
            for s in n['subnets']:
                subnet_id_choices.append((s.id, s.cidr))
        self.fields['vip_subnet_id'].choices = subnet_id_choices

        # provider choice
        try:
            if api.neutron.is_extension_supported(request, 'service-type'):
                provider_list = api.neutron.provider_list(request)
                providers = [p for p in provider_list
                             if p['service_type'] == 'LOADBALANCERV2']
            else:
                providers = None
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve providers list.'))
            providers = []

        if providers:
            default_providers = [p for p in providers if p.get('default')]
            if default_providers:
                default_provider = default_providers[0]['name']
            else:
                default_provider = None
            provider_choices = [(p['name'], p['name']) for p in providers
                                if p['name'] != default_provider]
            if default_provider:
                provider_choices.insert(
                    0, (default_provider,
                        _("%s (default)") % default_provider))
        else:
            if providers is None:
                msg = _("Provider for Load Balancer is not supported")
            else:
                msg = _("No provider is available")
            provider_choices = [('', msg)]
            self.fields['provider'].widget.attrs['readonly'] = True
        self.fields['provider'].choices = provider_choices

    class Meta(object):
        name = _("Add New Loadbalancer")
        permissions = ('openstack.services.network',)
        help_text = _("Create loadbalancer for current project.\n\n"
                      "Assign a name and description for the loadbalancer. "
                      "Choose one subnet where all members of this "
                      "pool must be on. "
                      "Select the protocol and load balancing method "
                      "for this pool. "
                      "Admin State is UP (checked) by default.")


class AddLoadbalancerStep(workflows.Step):
    action_class = AddLoadbalancerAction
    contributes = ("name", "description", "vip_subnet_id", "provider",
                   "vip_address", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddLoadbalancerStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddLoadbalancer(workflows.Workflow):
    slug = "addloadbalancer"
    name = _("Add Loadbalancer")
    finalize_button_name = _("Add")
    success_message = _('Added loadbalancer "%s".')
    failure_message = _('Unable to add loadbalancer "%s".')
    success_url = "horizon:user:loadbalancers:index"
    default_steps = (AddLoadbalancerStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            api.lbaas_v2.loadbalancer_create(request, **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False


class AddListenerAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))

    loadbalancer_id = forms.ChoiceField(label=_("Loadbalancer"))

    protocol = forms.ChoiceField(label=_("Protocol"))
    protocol_port = forms.IntegerField(
        label=_("Protocol Port"), min_value=1,
        help_text=_("Enter an integer value "
                    "between 1 and 65535."),
        validators=[validators.validate_port_range])

    connection_limit = forms.ChoiceField(
        choices = [(5000, 5000),
                   (10000, 10000),
                   (20000, 20000),
                   (40000, 40000)],
        label=_("Connection Limit"),
        help_text=_("Maximum number of connections allowed."))

    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddListenerAction, self).__init__(request, *args, **kwargs)
        tenant_id = request.user.tenant_id
        loadbalancer_choices = [('', _("Select a Loadbalancer"))]
        try:
            loadbalancers = api.lbaas_v2.loadbalancer_list(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve loadbalancer list.'))
            loadbalancers = []
        for l in loadbalancers:
            loadbalancer_choices.append((l.id, l.name))
        self.fields['loadbalancer_id'].choices = loadbalancer_choices

        protocol_choices = [('', _("Select a Protocol"))]
        [protocol_choices.append((p, p)) for p in AVAILABLE_PROTOCOLS]
        self.fields['protocol'].choices = protocol_choices

    class Meta(object):
        name = _("Add New Listener")
        permissions = ('openstack.services.network',)
        help_text = _("Create listener for current project.\n\n"
                      "Assign a name and description for the listener. "
                      "Choose one subnet where all members of this "
                      "pool must be on. "
                      "Select the protocol and load balancing method "
                      "for this pool. "
                      "Admin State is UP (checked) by default.")


class AddListenerStep(workflows.Step):
    action_class = AddListenerAction
    contributes = ("name", "description", "loadbalancer_id", "protocol",
                   "protocol_port", "connection_limit", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddListenerStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddListener(workflows.Workflow):
    slug = "addlistener"
    name = _("Add Listener")
    finalize_button_name = _("Add")
    success_message = _('Added listener "%s".')
    failure_message = _('Unable to add listener "%s".')
    success_url = "horizon:user:loadbalancers:index"
    default_steps = (AddListenerStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            api.lbaas_v2.listener_create(request, **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False


class AddPoolAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    listener_id = forms.ChoiceField(label=_("Listener"))
    lb_algorithm = forms.ChoiceField(label=_("Load Balancing Method"))
    protocol = forms.ChoiceField(label=_("Protocol"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddPoolAction, self).__init__(request, *args, **kwargs)
        tenant_id = request.user.tenant_id
        listener_choices = [('', _("Select a Loadbalancer"))]
        try:
            listeners = api.lbaas_v2.listener_list(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve listener list.'))
            listeners = []
        for l in listeners:
            listener_choices.append((l.id, l.name))
        self.fields['listener_id'].choices = listener_choices

        lb_algorithm_choices = [('', _("Select an Algorithm"))]
        [lb_algorithm_choices.append((m, m)) for m in AVAILABLE_METHODS]
        self.fields['lb_algorithm'].choices = lb_algorithm_choices

        protocol_choices = [('', _("Select a Protocol"))]
        [protocol_choices.append((p, p)) for p in AVAILABLE_PROTOCOLS]
        self.fields['protocol'].choices = protocol_choices

    class Meta(object):
        name = _("Add New Pool")
        permissions = ('openstack.services.network',)
        help_text = _("Create pool for current project.\n\n"
                      "Assign a name and description for the pool. "
                      "Choose one subnet where all members of this "
                      "pool must be on. "
                      "Select the protocol and load balancing method "
                      "for this pool. "
                      "Admin State is UP (checked) by default.")


class AddPoolStep(workflows.Step):
    action_class = AddPoolAction
    contributes = ("name", "description", "listener_id", "lb_algorithm",
                   "protocol", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddPoolStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddPool(workflows.Workflow):
    slug = "addpool"
    name = _("Add Pool")
    finalize_button_name = _("Add")
    success_message = _('Added pool "%s".')
    failure_message = _('Unable to add pool "%s".')
    success_url = "horizon:user:loadbalancers:index"
    default_steps = (AddPoolStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            api.lbaas_v2.pool_create(request, **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False


class AddMemberAction(workflows.Action):
    pool_id = forms.CharField(label=_("Pool"),
                              widget=forms.TextInput(
                                  attrs={'readonly': 'readonly'}))
    protocol_port = forms.IntegerField(
        label=_("Protocol Port"), min_value=1,
        help_text=_("Enter an integer value "
                    "between 1 and 65535."),
        validators=[validators.validate_port_range])
    weight = forms.IntegerField(
        max_value=256, min_value=1, label=_("Weight"), required=False,
        help_text=_("Relative part of requests this pool member serves "
                    "compared to others. \nThe same weight will be applied to "
                    "all the selected members and can be modified later. "
                    "Weight must be in the range 1 to 256.")
    )
    subnet_id = forms.ChoiceField(label=_("VIP Subnet"),
                                  required=False)
    address = forms.IPField(label=_("Specify a free IP address "
                                    "from the selected subnet"),
                            version=forms.IPv4,
                            mask=False)
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddMemberAction, self).__init__(request, *args, **kwargs)
        tenant_id = request.user.tenant_id
        subnet_id_choices = [('', _("Select a Subnet"))]
        try:
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve networks list.'))
            networks = []
        for n in networks:
            for s in n['subnets']:
                subnet_id_choices.append((s.id, s.cidr))
        self.fields['subnet_id'].choices = subnet_id_choices

    class Meta(object):
        name = _("Add New Member")
        permissions = ('openstack.services.network',)
        help_text = _("Create member for current project.\n\n"
                      "Assign a name and description for the member. "
                      "Choose one subnet where all members of this "
                      "member must be on. "
                      "Select the protocol and load balancing method "
                      "for this member. "
                      "Admin State is UP (checked) by default.")


class AddMemberStep(workflows.Step):
    action_class = AddMemberAction
    contributes = ("pool_id", "address", "protocol_port", "weight",
                   "subnet_id", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddMemberStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddMember(workflows.Workflow):
    slug = "addmember"
    name = _("Add Member")
    finalize_button_name = _("Add")
    success_message = _('Added member "%s".')
    failure_message = _('Unable to add member "%s".')
    success_url = "horizon:user:loadbalancers:index"
    default_steps = (AddMemberStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            api.lbaas_v2.member_create(request,
                                       **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False
