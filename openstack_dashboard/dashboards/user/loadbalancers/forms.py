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

    failure_url = 'horizon:user:loadbalancers:index'

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
