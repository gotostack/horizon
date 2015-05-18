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
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api


AVAILABLE_PROTOCOLS = ('TCP', 'HTTP', 'HTTPS', 'TERMINATED_HTTPS')
AVAILABLE_METHODS = ('ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP')

ENABLE_SPECIFY_LBV2_AGENT = getattr(settings,
                                    'ENABLE_SPECIFY_LBV2_AGENT',
                                    False)

NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$", re.UNICODE)
ACL_NAME_HELP_TEXT = _(
    'ACL name must begin with letter'
    ' and only contain letters, numbers and underline.'
    ' ACL name must be unique in same listener.')
ACL_NAME_ERROR_MESSAGES = {'invalid': ACL_NAME_HELP_TEXT}

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
                msg = _("Provider for Load Balancer V2 is not supported.")
            else:
                msg = _("No provider is available")
            provider_choices = [('', msg)]
            self.fields['provider'].widget.attrs['readonly'] = True
        self.fields['provider'].choices = provider_choices

        if ENABLE_SPECIFY_LBV2_AGENT:
            self.fields['agent'] = forms.ChoiceField(
                label=_("Agent Host"), required=False)
            agent_choices = [('', _("Select an Agent Host"))]
            try:
                agents = api.neutron.agent_list(request)
            except Exception:
                exceptions.handle(request,
                                  _('Unable to retrieve agent list.'))
                agents = []
            for a in agents:
                if a.agent_type == "Loadbalancerv2 agent":
                    agent_choices.append((a.id, a.host))
            self.fields['agent'].choices = agent_choices

    class Meta(object):
        name = _("Add New Loadbalancer")
        permissions = ('openstack.services.network',)
        help_text = _("Create loadbalancer for current project.\n\n"
                      "Assign a name and description for the loadbalancer. "
                      "Choose one subnet where you can get the"
                      " loadbalancer VIP. \n\n"
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
        choices=[('5000', '5000'),
                 ('10000', '10000'),
                 ('20000', '20000'),
                 ('40000', '40000')],
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
            loadbalancers = api.lbaas_v2.loadbalancer_list(
                request, tenant_id=tenant_id)
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
        help_text = _("Create a listener for specific loadbalancer.\n\n"
                      "Assign a name and description for the listener. "
                      "Select the protocol, port,  and connection limit "
                      "for this listener. "
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
        listener_choices = [('', _("Select a Listener"))]
        try:
            listeners = api.lbaas_v2.listener_list(request,
                                                   tenant_id=tenant_id)
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
        help_text = _("Create a pool for specific listener.\n\n"
                      "Assign a name and description for the pool. "
                      "Select the protocol and load balancing algorithm "
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
                                  # temporarily set to required
                                  required=True)
    address = forms.IPField(label=_("Input An Service IP address"),
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
        help_text = _("Create a member for specific pool.\n\n"
                      "Set the weight of this member. "
                      "Set the member service port and IP. "
                      "Choose one subnet where this member is on. "
                      "Address is the member service IP."
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
    success_url = "horizon:user:loadbalancers:pooldetails"
    default_steps = (AddMemberStep,)

    def get_success_url(self):
        pool_id = self.context.get('pool_id')
        return reverse(self.success_url, args=(pool_id,))

    def format_status_message(self, message):
        address = self.context.get('address')
        return message % address

    def handle(self, request, context):
        try:
            api.lbaas_v2.member_create(request,
                                       **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False


class AddAclAction(workflows.Action):
    listener_id = forms.CharField(label=_("Listener"),
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    name = forms.RegexField(max_length=80,
                            label=_("ACL Name"),
                            regex=NAME_REGEX,
                            error_messages=ACL_NAME_ERROR_MESSAGES,
                            help_text=ACL_NAME_HELP_TEXT)
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    action = forms.CharField(
        max_length=80, label=_("ACL Action"))
    condition = forms.CharField(
        max_length=80, label=_("ACL Condition"))
    acl_type = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("ACL Type"))
    operator = forms.CharField(
        max_length=80, label=_("ACL Operator"))
    match = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("ACL Match"))
    match_condition = forms.CharField(
        max_length=80, label=_("ACL Match condition"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddAclAction, self).__init__(request, *args, **kwargs)

    class Meta(object):
        name = _("Add New ACL")
        permissions = ('openstack.services.network',)
        help_text = _("Create an acl for specific listener.\n\n"
                      "A complete haproxy acl is assembled like:\n\n"
                      "acl [ACL Name] [ACL Action] [ACL Condition]\n\n"
                      "[ACL Operator] [ACL Match] if [ACL Match condition]\n\n"
                      "Admin State is UP (checked) by default.")


class AddAclStep(workflows.Step):
    action_class = AddAclAction
    contributes = ("listener_id", "name", "description", "action",
                   "condition", "acl_type", "operator",
                   "match", "match_condition", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddAclStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddAcl(workflows.Workflow):
    slug = "addacl"
    name = _("Add ACL")
    finalize_button_name = _("Add")
    success_message = _('Added acl "%s".')
    failure_message = _('Unable to add acl "%s".')
    success_url = "horizon:user:loadbalancers:listenerdetails"
    default_steps = (AddAclStep,)

    def get_success_url(self):
        listener_id = self.context.get('listener_id')
        return reverse(self.success_url, args=(listener_id,))

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            api.lbaas_v2.acl_create(request,
                                    **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False


class AddHealthmonitorAction(workflows.Action):
    pool_id = forms.ChoiceField(label=_("Pool"))
    type = forms.ChoiceField(
        label=_("Type"),
        choices=[('ping', _('PING')),
                 ('tcp', _('TCP')),
                 ('http', _('HTTP')),
                 ('https', _('HTTPS'))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'type'
        }))
    delay = forms.IntegerField(
        min_value=1,
        label=_("Delay"),
        help_text=_("The minimum time in seconds between regular checks "
                    "of a member"))
    timeout = forms.IntegerField(
        min_value=1,
        label=_("Timeout"),
        help_text=_("The maximum time in seconds for a monitor to wait "
                    "for a reply"))
    max_retries = forms.IntegerField(
        max_value=10, min_value=1,
        label=_("Max Retries (1~10)"),
        help_text=_("Number of permissible failures before changing "
                    "the status of member to inactive"))
    http_method = forms.ChoiceField(
        initial="GET",
        required=False,
        choices=[('GET', _('GET'))],
        label=_("HTTP Method"),
        help_text=_("HTTP method used to check health status of a member"),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'type',
            'data-type-http': _('HTTP Method'),
            'data-type-https': _('HTTP Method')
        }))
    url_path = forms.CharField(
        initial="/",
        required=False,
        max_length=80,
        label=_("URL"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'type',
            'data-type-http': _('URL'),
            'data-type-https': _('URL')
        }))
    expected_codes = forms.RegexField(
        initial="200",
        required=False,
        max_length=80,
        regex=r'^(\d{3}(\s*,\s*\d{3})*)$|^(\d{3}-\d{3})$',
        label=_("Expected HTTP Status Codes"),
        help_text=_("Expected code may be a single value (e.g. 200), "
                    "a list of values (e.g. 200, 202), "
                    "or range of values (e.g. 200-204)"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'type',
            'data-type-http': _('Expected HTTP Status Codes'),
            'data-type-https': _('Expected HTTP Status Codes')
        }))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddHealthmonitorAction, self).__init__(request, *args, **kwargs)
        tenant_id = request.user.tenant_id
        pool_id_choices = [('', _("Select a Pool"))]
        try:
            pools = api.lbaas_v2.pool_list(request,
                                           tenant_id=tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve pool list.'))
            pools = []
        for p in pools:
            pool_id_choices.append((p.id, p.name))
        self.fields['pool_id'].choices = pool_id_choices

    def clean(self):
        cleaned_data = super(AddHealthmonitorAction, self).clean()
        type_opt = cleaned_data.get('type')
        delay = cleaned_data.get('delay')
        timeout = cleaned_data.get('timeout')

        if not delay >= timeout:
            msg = _('Delay must be greater than or equal to Timeout')
            self._errors['delay'] = self.error_class([msg])

        if type_opt in ['http', 'https']:
            http_method_opt = cleaned_data.get('http_method')
            url_path = cleaned_data.get('url_path')
            expected_codes = cleaned_data.get('expected_codes')

            if not http_method_opt:
                msg = _('Please choose a HTTP method')
                self._errors['http_method'] = self.error_class([msg])
            if not url_path:
                msg = _('Please specify an URL')
                self._errors['url_path'] = self.error_class([msg])
            if not expected_codes:
                msg = _('Please enter a single value (e.g. 200), '
                        'a list of values (e.g. 200, 202), '
                        'or range of values (e.g. 200-204)')
                self._errors['expected_codes'] = self.error_class([msg])
        return cleaned_data

    class Meta(object):
        name = _("Add New Monitor")
        permissions = ('openstack.services.network',)
        help_text = _("Create a monitor template.\n\n"
                      "Select type of monitoring. "
                      "Specify delay, timeout, and retry limits "
                      "required by the monitor. "
                      "Specify method, URL path, and expected "
                      "HTTP codes upon success.")


class AddHealthmonitorStep(workflows.Step):
    action_class = AddHealthmonitorAction
    contributes = ("pool_id", "type", "delay", "timeout", "max_retries",
                   "http_method", "url_path", "expected_codes",
                   "admin_state_up")

    def contribute(self, data, context):
        context = super(AddHealthmonitorStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddHealthmonitor(workflows.Workflow):
    slug = "addmonitor"
    name = _("Add Monitor")
    finalize_button_name = _("Add")
    success_message = _('Added monitor')
    failure_message = _('Unable to add monitor')
    success_url = "horizon:user:loadbalancers:index"
    default_steps = (AddHealthmonitorStep,)

    def handle(self, request, context):
        try:
            api.lbaas_v2.healthmonitor_create(request,
                                              **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False


class AddRedundanceAction(workflows.Action):
    loadbalancer_id = forms.CharField(label=_("Loadbalancer"),
                                      widget=forms.TextInput(
                                          attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length=80,
                           required=False,
                           initial="",
                           label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddRedundanceAction, self).__init__(request, *args, **kwargs)

        if ENABLE_SPECIFY_LBV2_AGENT:
            self.fields['agent_id'] = forms.ChoiceField(
                label=_("Agent Host"), required=False)
            agent_choices = [('', _("Select an Agent Host"))]
            try:
                agents = api.neutron.agent_list(request)
            except Exception:
                exceptions.handle(request,
                                  _('Unable to retrieve agent list.'))
                agents = []
            for a in agents:
                if a.agent_type == "Loadbalancerv2 agent":
                    agent_choices.append((a.id, a.host))
            self.fields['agent_id'].choices = agent_choices

    class Meta(object):
        name = _("Add New Redundance")
        permissions = ('openstack.services.network',)
        help_text = _("Create a redundance for specific loadbalancer.\n\n"
                      "A haproxy instance will be create"
                      " in a different agent host. "
                      "Admin State is UP (checked) by default.")


class AddRedundanceStep(workflows.Step):
    action_class = AddRedundanceAction
    contributes = ("loadbalancer_id", "name", "description", "agent_id",
                   "admin_state_up")

    def contribute(self, data, context):
        context = super(AddRedundanceStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddRedundance(workflows.Workflow):
    slug = "addredundance"
    name = _("Add Redundance")
    finalize_button_name = _("Add")
    success_message = _('Added redundance "%s".')
    failure_message = _('Unable to add redundance "%s".')
    success_url = "horizon:user:loadbalancers:loadbalancerdetails"
    default_steps = (AddRedundanceStep,)

    def get_success_url(self):
        loadbalancer_id = self.context.get('loadbalancer_id')
        return reverse(self.success_url, args=(loadbalancer_id,))

    def format_status_message(self, message):
        address = self.context.get('address')
        return message % address

    def handle(self, request, context):
        try:
            api.lbaas_v2.redundance_create(request, **context)
            return True
        except Exception as e:
            exceptions.handle(request, e)
            return False
