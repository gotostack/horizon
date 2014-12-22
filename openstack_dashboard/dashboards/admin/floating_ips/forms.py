# Copyright 2014 Letv Cloud Computing
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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class AdminFloatingIpAllocate(forms.SelfHandlingForm):
    pool = forms.ChoiceField(label=_("Pool"))
    tenant = forms.ChoiceField(label=_("Project"))

    def __init__(self, *args, **kwargs):
        super(AdminFloatingIpAllocate, self).__init__(*args, **kwargs)
        floating_pool_list = kwargs.get('initial', {}).get('pool_list', [])
        self.fields['pool'].choices = floating_pool_list
        tenant_list = kwargs.get('initial', {}).get('tenant_list', [])
        self.fields['tenant'].choices = tenant_list

    def handle(self, request, data):
        try:
            # Admin ignore quota
            fip = api.network.tenant_floating_ip_allocate(
                request,
                pool=data['pool'],
                tenant_id=data['tenant'])
            messages.success(
                request,
                _('Allocated Floating IP %(ip)s.') % {"ip": fip.ip})
            return fip
        except Exception:
            redirect = reverse('horizon:admin:floating_ips:index')
            msg = _('Unable to allocate Floating IP.')
            exceptions.handle(request, msg, redirect=redirect)
