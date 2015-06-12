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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)

AVAILABLE_METHODS = ('ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP')


class UpdateBase(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"),
                         widget=forms.TextInput(
                             attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(required=False,
                                  max_length=80, label=_("Description"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    failure_url = 'horizon:manager:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateBase, self).__init__(request, *args, **kwargs)


class UpdateLoadbalancer(UpdateBase):

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            lb = api.lbaas_v2.loadbalancer_update(request,
                                                  context['id'],
                                                  **context)
            msg = _(
                'Loadbalancer %s was successfully updated.') % context['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return lb
        except Exception:
            msg = _('Failed to update loadbalancer %s') % context['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateListener(UpdateBase):
    connection_limit = forms.IntegerField(
        min_value=-1, label=_("Connection Limit"),
        help_text=_("Maximum number of connections allowed "
                    "for the loadbalancer or '-1' if the limit is not set"))

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            lb = api.lbaas_v2.listener_update(request,
                                              context['id'],
                                              **context)
            msg = _(
                'Listener %s was successfully updated.') % context['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return lb
        except Exception:
            msg = _('Failed to update listener %s') % context['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdatePool(UpdateBase):
    lb_algorithm = forms.ChoiceField(label=_("Load Balancing Method"))

    def __init__(self, request, *args, **kwargs):
        super(UpdateBase, self).__init__(request, *args, **kwargs)

        lb_algorithm_choices = [('', _("Select an Algorithm"))]
        [lb_algorithm_choices.append((m, m)) for m in AVAILABLE_METHODS]
        self.fields['lb_algorithm'].choices = lb_algorithm_choices

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            lb = api.lbaas_v2.pool_update(request,
                                          context['id'],
                                          **context)
            msg = _(
                'Pool %s was successfully updated.') % context['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return lb
        except Exception:
            msg = _('Failed to update pool %s') % context['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateMember(forms.SelfHandlingForm):
    member_id = forms.CharField(label=_("ID"),
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))
    pool_id = forms.CharField(label=_("Pool"),
                              widget=forms.TextInput(
                                  attrs={'readonly': 'readonly'}))
    weight = forms.IntegerField(
        max_value=256, min_value=1, label=_("Weight"), required=False,
        help_text=_("Relative part of requests this pool member serves "
                    "compared to others. \nThe same weight will be applied to "
                    "all the selected members and can be modified later. "
                    "Weight must be in the range 1 to 256.")
    )
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    failure_url = 'horizon:manager:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateMember, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            member = api.lbaas_v2.member_update(request,
                                                **context)
            msg = _('Member %s was successfully updated.')\
                % context['member_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return member
        except Exception:
            msg = _('Failed to update member %s') % context['member_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateAcl(forms.SelfHandlingForm):
    listener_id = forms.CharField(label=_("Listener"),
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    acl_id = forms.CharField(label=_("ACL ID"),
                             widget=forms.TextInput(
                                 attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length=80, label=_("Name"))
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

    failure_url = 'horizon:manager:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateAcl, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            acl = api.lbaas_v2.acl_update(request,
                                          **context)
            msg = _('ACL %s was successfully updated.')\
                % context['acl_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return acl
        except Exception:
            msg = _('Failed to update acl %s') % context['acl_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateHealthmonitor(forms.SelfHandlingForm):
    healthmonitor_id = forms.CharField(label=_("ID"),
                                       widget=forms.TextInput(
                                           attrs={'readonly': 'readonly'}))
    type = forms.ChoiceField(
        label=_("Type"),
        choices=[('ping', _('PING')),
                 ('tcp', _('TCP')),
                 ('http', _('HTTP')),
                 ('https', _('HTTPS'))],
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}))
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

    failure_url = 'horizon:manager:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateHealthmonitor, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            healthmonitor = api.lbaas_v2.healthmonitor_update(request,
                                                              **context)
            msg = _('Healthmonitor %s was successfully updated.')\
                % context['healthmonitor_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return healthmonitor
        except Exception:
            msg = _('Failed to update healthmonitor %s')\
                % context['healthmonitor_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateRedundance(forms.SelfHandlingForm):
    redundance_id = forms.CharField(label=_("ID"),
                                    widget=forms.TextInput(
                                        attrs={'readonly': 'readonly'}))
    loadbalancer_id = forms.CharField(label=_("Loadbalancer"),
                                      widget=forms.TextInput(
                                          attrs={'readonly': 'readonly'}))
    refresh = forms.ChoiceField(
        initial='false',
        required=False,
        choices=[('true', _('True')),
                 ('false', _('False'))],
        label=_("Refresh"),
        help_text=_("Refresh a load balancer"
                    " redundance haproxy config file."),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'refresh'
        }))
    name = forms.CharField(
        max_length=80,
        label=_("Name"),
        required=False,
        initial="",
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'refresh',
            'data-refresh-false': _('Name')
        }))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'refresh',
            'data-refresh-false': _('Description')
        }))
    admin_state_up = forms.ChoiceField(
        choices=[(True, _('UP')),
                 (False, _('DOWN'))],
        label=_("Admin State"))

    failure_url = 'horizon:manager:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateRedundance, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            redundance = api.lbaas_v2.redundance_update(request,
                                                        **context)
            msg = _('Redundance %s was successfully updated.')\
                % context['redundance_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return redundance
        except Exception:
            msg = _(
                'Failed to update redundance %s') % context['redundance_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)


class UpdateLVSPort(forms.SelfHandlingForm):
    lvs_id = forms.CharField(label=_("Loadbalancer"),
                             widget=forms.TextInput(
                                 attrs={'readonly': 'readonly'}))
    name = forms.CharField(
        max_length=80,
        label=_("Name"),
        required=False,
        initial="")
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    admin_state_up = forms.ChoiceField(
        choices=[(True, _('UP')),
                 (False, _('DOWN'))],
        label=_("Admin State"))

    failure_url = 'horizon:manager:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateLVSPort, self).__init__(request, *args, **kwargs)

    def handle(self, request, context):
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        try:
            lvsport = api.lbaas_v2.lvsport_update(request,
                                                  **context)
            msg = _('LVS Port %s was successfully updated.') \
                % context['lvs_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return lvsport
        except Exception:
            msg = _(
                'Failed to update LVS Port %s') % context['lvs_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
