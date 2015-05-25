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

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.manager import dashboard

LOG = logging.getLogger(__name__)


class AdminFloatingIps(horizon.Panel):
    name = _("Floating IPs")
    slug = 'floating_ips'
    permissions = ('openstack.roles.admin', 'openstack.services.network', )


network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
if network_config.get('enable_router', True):
    dashboard.Manager.register(AdminFloatingIps)
