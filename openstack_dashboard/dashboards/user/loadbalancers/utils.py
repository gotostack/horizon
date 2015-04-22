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

from horizon import exceptions
from horizon.utils import memoized

from openstack_dashboard import api


def get_monitor_display_name(monitor):
    fields = ['type', 'delay', 'max_retries', 'timeout']
    if monitor.type in ['HTTP', 'HTTPS']:
        fields.extend(['url_path', 'expected_codes', 'http_method'])
        name = _("%(type)s: url:%(url_path)s "
                 "method:%(http_method)s codes:%(expected_codes)s "
                 "delay:%(delay)d retries:%(max_retries)d "
                 "timeout:%(timeout)d")
    else:
        name = _("%(type)s delay:%(delay)d "
                 "retries:%(max_retries)d "
                 "timeout:%(timeout)d")
    params = dict((key, getattr(monitor, key)) for key in fields)
    return name % params


@memoized.memoized_method
def get_subnets(request):
    try:
        subnets = api.neutron.subnet_list(request)
    except Exception:
        subnets = []
        exceptions.handle(request,
                          _('Unable to retrieve subnet list.'))
    return subnets


@memoized.memoized_method
def get_loadbalancers(request):
    try:
        loadbalancers = api.lbaas_v2.loadbalancer_list(request)
    except Exception:
        loadbalancers = []
        exceptions.handle(request,
                          _('Unable to retrieve loadbalancer list.'))
    return loadbalancers


@memoized.memoized_method
def get_listeners(request):
    try:
        listeners = api.lbaas_v2.listener_list(request)
    except Exception:
        listeners = []
        exceptions.handle(request,
                          _('Unable to retrieve listener list.'))
    return listeners


@memoized.memoized_method
def get_pools(request):
    try:
        pools = api.lbaas_v2.pool_list(request)
    except Exception:
        pools = []
        exceptions.handle(request,
                          _('Unable to retrieve pool list.'))
    return pools


@memoized.memoized_method
def get_healthmonitors(request):
    try:
        healthmonitors = api.lbaas_v2.healthmonitor_list(request)
    except Exception:
        healthmonitors = []
        exceptions.handle(request,
                          _('Unable to retrieve healthmonitor list.'))
    return healthmonitors
