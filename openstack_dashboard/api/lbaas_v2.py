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

from __future__ import absolute_import

from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import neutron

neutronclient = neutron.neutronclient


class Acl(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer v2 ACL."""

    def __init__(self, apiresource):
        super(Acl, self).__init__(apiresource)


class Healthmonitor(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer v2 Healthmonitor."""

    def __init__(self, apiresource):
        super(Healthmonitor, self).__init__(apiresource)


class Listener(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer v2 Loadbalancer."""

    def __init__(self, apiresource):
        super(Listener, self).__init__(apiresource)


class Loadbalancer(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer v2 Loadbalancer."""

    def __init__(self, apiresource):
        super(Loadbalancer, self).__init__(apiresource)


class Member(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer v2 member."""

    def __init__(self, apiresource):
        super(Member, self).__init__(apiresource)


class Pool(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer v2 pool."""

    def __init__(self, apiresource):
        if 'provider' not in apiresource:
            apiresource['provider'] = None
        super(Pool, self).__init__(apiresource)


class LoadbalancerStats(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer stats."""

    def __init__(self, apiresource):
        super(LoadbalancerStats, self).__init__(apiresource)


class LoadbalancerStatuses(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer statuses."""

    def __init__(self, apiresource):
        super(LoadbalancerStatuses, self).__init__(apiresource)


class LbRedundance(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer Redundance."""

    def __init__(self, apiresource):
        super(LbRedundance, self).__init__(apiresource)


class LbRedundanceStats(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer Redundance stats."""

    def __init__(self, apiresource):
        super(LbRedundanceStats, self).__init__(apiresource)


class LVSPort(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer LVS port."""

    def __init__(self, apiresource):
        super(LVSPort, self).__init__(apiresource)


def get_agent_hosting_loadbalancer(request, loadbalancer_id, **kwargs):
    """Get lbaas v2 agent hosting a loadbalancer.

    return agent that placed the loadbalancer on, and show the agent
    status, host, heartbeat etc.
    """
    agent = neutronclient(
        request).get_lbaas_agent_hosting_loadbalancer(
            loadbalancer_id, **kwargs).get('agent')
    return neutron.Agent(agent)


def get_loadbalancer_list_on_agent(request, agent_id, **kwargs):
    """List the loadbalancers on a loadbalancer v2 agent.

    return the list of loadbalancers on a specific lbaas v2 agent.
    """
    loadbalancers = neutronclient(
        request).list_loadbalancers_on_lbaas_agent(
            agent_id, **kwargs).get('loadbalancers')
    return [Loadbalancer(l) for l in loadbalancers]


def loadbalancer_create(request, **kwargs):
    """LBaaS v2 Create a loadbalancer."""
    body = {'loadbalancer': {
        'name': kwargs['name'],
        'description': kwargs['description'],
        'vip_subnet_id': kwargs['vip_subnet_id'],
        'admin_state_up': kwargs['admin_state_up'],
        'provider': kwargs['provider']}}
    if kwargs.get('vip_address'):
        body['loadbalancer']['vip_address'] = kwargs['vip_address']
    if kwargs.get('agent'):
        body['loadbalancer']['agent'] = kwargs['agent']
    if kwargs.get('tenant_id'):
        body['loadbalancer']['tenant_id'] = kwargs['tenant_id']
    loadbalancer = neutronclient(
        request).create_loadbalancer(body).get('loadbalancer')
    return Loadbalancer(loadbalancer)


def loadbalancer_delete(request, loadbalancer_id):
    """LBaaS v2 Delete a given loadbalancer."""
    neutronclient(request).delete_loadbalancer(loadbalancer_id)


@memoized
def loadbalancer_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List loadbalancers that belong to a given tenant."""
    loadbalancers = neutronclient(
        request).list_lbaas_loadbalancers(retrieve_all,
                                          **kwargs).get('loadbalancers')
    return [Loadbalancer(l) for l in loadbalancers]


@memoized
def loadbalancer_get(request, loadbalancer_id, **kwargs):
    """LBaaS v2 Show information of a given loadbalancer."""
    loadbalancer = neutronclient(
        request).show_loadbalancer(loadbalancer_id,
                                   **kwargs).get('loadbalancer')
    return Loadbalancer(loadbalancer)


def loadbalancer_update(request, loadbalancer_id, **kwargs):
    """LBaaS v2 Update a given loadbalancer."""
    body = {'loadbalancer': {
        'name': kwargs['name'],
        'description': kwargs['description'],
        'admin_state_up': kwargs['admin_state_up']}}
    loadbalancer = neutronclient(
        request).update_loadbalancer(loadbalancer_id,
                                     body).get('loadbalancer')
    return Loadbalancer(loadbalancer)


def loadbalancer_stats(request, loadbalancer_id, **kwargs):
    """LBaaS v2 retrieve loadbalancer stats."""
    stats = neutronclient(request).retrieve_loadbalancer_stats(
        loadbalancer_id, **kwargs).get('stats')
    return LoadbalancerStats(stats)


def loadbalancer_statuses(request, loadbalancer_id, **kwargs):
    """LBaaS v2 retrieve loadbalancer statuses."""
    statuses = neutronclient(request).retrieve_loadbalancer_statuses(
        loadbalancer_id, **kwargs).get('statuses')
    return LoadbalancerStatuses(statuses)


def listener_create(request, **kwargs):
    """LBaaS v2 Create a listener."""
    body = {"listener": {
        'name': kwargs['name'],
        'description': kwargs['description'],
        "loadbalancer_id": kwargs['loadbalancer_id'],
        "protocol_port": kwargs['protocol_port'],
        "protocol": kwargs['protocol'],
        'admin_state_up': kwargs['admin_state_up']}}
    if kwargs.get('tenant_id'):
        body['listener']['tenant_id'] = kwargs['tenant_id']
    listener = neutronclient(
        request).create_listener(body).get('listener')
    return Listener(listener)


def listener_delete(request, listener_id):
    """LBaaS v2 Delete a given listener."""
    neutronclient(request).delete_listener(listener_id)


@memoized
def listener_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List listeners that belong to a given tenant."""
    listeners = neutronclient(
        request).list_listeners(retrieve_all,
                                **kwargs).get('listeners')
    return [Listener(l) for l in listeners]


@memoized
def listener_get(request, listener_id, **kwargs):
    """LBaaS v2 Show information of a given listener."""
    listener = neutronclient(
        request).show_listener(listener_id,
                               **kwargs).get('listener')
    return Listener(listener)


def listener_update(request, listener_id, **kwargs):
    """LBaaS v2 Update a given listener."""
    body = {"listener": {
        'name': kwargs['name'],
        'description': kwargs['description'],
        'connection_limit': kwargs['connection_limit'],
        'admin_state_up': kwargs['admin_state_up']}}
    listener = neutronclient(
        request).update_listener(listener_id,
                                 body).get('listener')
    return Listener(listener)


def pool_create(request, **kwargs):
    """LBaaS v2 Create a pool."""
    body = {
        "pool": {
            "description": kwargs['description'],
            "lb_algorithm": kwargs['lb_algorithm'],
            "listener_id": kwargs['listener_id'],
            "protocol": kwargs['protocol'],
            "name": kwargs['name'],
            "admin_state_up": kwargs['admin_state_up']
        }
    }
    if kwargs.get('tenant_id'):
        body['pool']['tenant_id'] = kwargs['tenant_id']
    pool = neutronclient(
        request).create_lbaas_pool(body).get('pool')
    return Pool(pool)


def pool_delete(request, pool_id):
    """LBaaS v2 Delete a given pool."""
    neutronclient(request).delete_lbaas_pool(pool_id)


@memoized
def pool_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List pools that belong to a given tenant."""
    pools = neutronclient(
        request).list_lbaas_pools(retrieve_all,
                                  **kwargs).get('pools')
    return [Pool(p) for p in pools]


@memoized
def pool_get(request, pool_id, **kwargs):
    """LBaaS v2 Show information of a given pool."""
    pool = neutronclient(
        request).show_lbaas_pool(pool_id,
                                 **kwargs).get('pool')
    return Pool(pool)


def pool_update(request, pool_id, **kwargs):
    """LBaaS v2 Update a given pool."""
    body = {
        "pool": {
            "name": kwargs['name'],
            "lb_algorithm": kwargs['lb_algorithm'],
            "description": kwargs['description'],
            "admin_state_up": kwargs['admin_state_up']
        }
    }
    pool = neutronclient(
        request).update_lbaas_pool(pool_id,
                                   body).get('pool')
    return Pool(pool)


def member_create(request, pool_id, **kwargs):
    """LBaaS v2 Create a member."""
    body = {"member": {
        "admin_state_up": kwargs['admin_state_up'],
        "subnet_id": kwargs['subnet_id'],
        "address": kwargs['address'],
        "protocol_port": kwargs['protocol_port']}}
    if kwargs['weight']:
        body['member']['weight'] = kwargs['weight']
    if kwargs['subnet_id']:
        body['member']['subnet_id'] = kwargs['subnet_id']
    if kwargs.get('tenant_id'):
        body['member']['tenant_id'] = kwargs['tenant_id']
    member = neutronclient(
        request).create_lbaas_member(pool_id,
                                     body).get('member')
    return Member(member)


def member_delete(request, member_id, pool_id):
    """LBaaS v2 Delete a given member."""
    neutronclient(request).delete_lbaas_member(member_id, pool_id)


@memoized
def member_list(request, pool, retrieve_all=True, **kwargs):
    """LBaaS v2 List members that belong to a given tenant."""
    members = neutronclient(
        request).list_lbaas_members(pool,
                                    retrieve_all,
                                    **kwargs).get('members')
    return [Member(m) for m in members]


@memoized
def member_get(request, member_id, pool_id, **kwargs):
    """LBaaS v2 Show information of a given member."""
    member = neutronclient(
        request).show_lbaas_member(member_id,
                                   pool_id,
                                   **kwargs).get('member')
    return Member(member)


def member_update(request, member_id, pool_id, **kwargs):
    """LBaaS v2 Update a given member."""
    body = {"member": {"admin_state_up": kwargs['admin_state_up']}}
    if kwargs['weight']:
        body['member']['weight'] = kwargs['weight']

    member = neutronclient(
        request).update_lbaas_member(member_id,
                                     pool_id,
                                     body).get('member')
    return Member(member)


def healthmonitor_create(request, **kwargs):
    """LBaaS v2 Create a healthmonitor."""
    monitor_type = kwargs['type'].upper()
    body = {
        "healthmonitor": {
            "pool_id": kwargs['pool_id'],
            "type": monitor_type,
            "delay": kwargs['delay'],
            "timeout": kwargs['timeout'],
            "max_retries": kwargs['max_retries'],
            "admin_state_up": kwargs['admin_state_up']
        }
    }
    if monitor_type in ['HTTP', 'HTTPS']:
        body['healthmonitor']['http_method'] = kwargs['http_method']
        body['healthmonitor']['url_path'] = kwargs['url_path']
        body['healthmonitor']['expected_codes'] = kwargs['expected_codes']
    if kwargs.get('tenant_id'):
        body['healthmonitor']['tenant_id'] = kwargs['tenant_id']
    healthmonitor = neutronclient(
        request).create_lbaas_healthmonitor(body).get('healthmonitor')
    return Healthmonitor(healthmonitor)


def healthmonitor_delete(request, healthmonitor_id):
    """LBaaS v2 Delete a given healthmonitor."""
    neutronclient(request).delete_lbaas_healthmonitor(healthmonitor_id)


@memoized
def healthmonitor_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List healthmonitors that belong to a given tenant."""
    healthmonitors = neutronclient(
        request).list_lbaas_healthmonitors(retrieve_all,
                                           **kwargs).get('healthmonitors')
    return [Healthmonitor(h) for h in healthmonitors]


@memoized
def healthmonitor_get(request, healthmonitor_id, **kwargs):
    """LBaaS v2 Show information of a given healthmonitor."""
    healthmonitor = neutronclient(
        request).show_lbaas_healthmonitor(healthmonitor_id,
                                          **kwargs).get('healthmonitor')
    return Healthmonitor(healthmonitor)


def healthmonitor_update(request, healthmonitor_id, **kwargs):
    """LBaaS v2 Update a given healthmonitor."""
    monitor_type = kwargs['type'].upper()
    body = {
        "healthmonitor": {
            "delay": kwargs['delay'],
            "timeout": kwargs['timeout'],
            "max_retries": kwargs['max_retries'],
            "admin_state_up": kwargs['admin_state_up']
        }
    }
    if monitor_type in ['HTTP', 'HTTPS']:
        body['healthmonitor']['http_method'] = kwargs['http_method']
        body['healthmonitor']['url_path'] = kwargs['url_path']
        body['healthmonitor']['expected_codes'] = kwargs['expected_codes']
    healthmonitor = neutronclient(
        request).update_lbaas_healthmonitor(healthmonitor_id,
                                            body).get('healthmonitor')
    return Healthmonitor(healthmonitor)


def acl_create(request, **kwargs):
    """LBaaS v2 Create an acl."""
    body = {
        "acl": {
            "name": kwargs['name'],
            "description": kwargs['description'],
            "admin_state_up": kwargs['admin_state_up'],
            "match_condition": kwargs['match_condition'],
            "listener_id": kwargs['listener_id'],
            "operator": kwargs['operator'],
            "match": kwargs['match'],
            "action": kwargs['action'],
            "acl_type": kwargs['acl_type'],
            "condition": kwargs['condition'],
        }
    }
    if kwargs.get('tenant_id'):
        body['acl']['tenant_id'] = kwargs['tenant_id']
    acl = neutronclient(
        request).create_acl(body).get('acl')
    return Acl(acl)


def acl_delete(request, acl_id):
    """LBaaS v2 Delete a given acl."""
    neutronclient(request).delete_acl(acl_id)


@memoized
def acl_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List acls that belong to a given tenant."""
    acls = neutronclient(
        request).list_acls(retrieve_all,
                           **kwargs).get('acls')
    return [Acl(a) for a in acls]


@memoized
def acl_get(request, acl_id, **kwargs):
    """LBaaS v2 Show information of a given acl."""
    acl = neutronclient(
        request).show_acl(acl_id,
                          **kwargs).get('acl')
    return Acl(acl)


def acl_update(request, acl_id, **kwargs):
    """LBaaS v2 Update a given acl."""
    body = {
        "acl": {
            "name": kwargs['name'],
            "description": kwargs['description'],
            "admin_state_up": kwargs['admin_state_up'],
            "match_condition": kwargs['match_condition'],
            "operator": kwargs['operator'],
            "match": kwargs['match'],
            "action": kwargs['action'],
            "acl_type": kwargs['acl_type'],
            "condition": kwargs['condition'],
        }
    }
    acl = neutronclient(
        request).update_acl(acl_id,
                            body).get('acl')
    return Acl(acl)


def redundance_create(request, loadbalancer_id, **kwargs):
    """LBaaS v2 Create a redundance."""
    body = {"redundance": {
        "admin_state_up": kwargs['admin_state_up'],
        "name": kwargs['name'],
        "description": kwargs['description']}}
    if (kwargs['agent_id']
            and kwargs['agent_id'] != ''):
        body['redundance']['agent_id'] = kwargs['agent_id']
    else:
        body['redundance']['agent_id'] = None
    if kwargs.get('tenant_id'):
        body['redundance']['tenant_id'] = kwargs['tenant_id']
    redundance = neutronclient(
        request).create_lbaas_redundance(loadbalancer_id,
                                         body).get('redundance')
    return LbRedundance(redundance)


def redundance_delete(request, redundance_id, loadbalancer_id):
    """LBaaS v2 Delete a given redundance."""
    neutronclient(request).delete_lbaas_redundance(redundance_id,
                                                   loadbalancer_id)


@memoized
def redundance_list(request, loadbalancer_id, retrieve_all=True, **kwargs):
    """LBaaS v2 List redundances that belong to a given tenant."""
    redundances = neutronclient(
        request).list_lbaas_redundances(loadbalancer_id,
                                        retrieve_all,
                                        **kwargs).get('redundances')
    return [LbRedundance(m) for m in redundances]


@memoized
def redundance_get(request, redundance_id, loadbalancer_id, **kwargs):
    """LBaaS v2 Show information of a given redundance."""
    redundance = neutronclient(
        request).show_lbaas_redundance(redundance_id,
                                       loadbalancer_id,
                                       **kwargs).get('redundance')
    return LbRedundance(redundance)


def redundance_update(request,
                      redundance_id,
                      loadbalancer_id,
                      refresh='false',
                      **kwargs):
    """LBaaS v2 Update or Refresh a given redundance."""
    body = {"redundance": {}}
    if refresh == 'true':
            redundance = neutronclient(
                request).update_lbaas_redundance(redundance_id,
                                                 loadbalancer_id,
                                                 body).get('redundance')
    else:
        body["redundance"] = {
            "admin_state_up": kwargs['admin_state_up'],
            "name": kwargs['name'],
            "description": kwargs['description']}

        redundance = neutronclient(
            request).update_lbaas_redundance(redundance_id,
                                             loadbalancer_id,
                                             body).get('redundance')
    return LbRedundance(redundance)


def lvsport_create(request, **kwargs):
    """LBaaS v2 Create a lvs port."""
    body = {"lvs": {
        "admin_state_up": kwargs['admin_state_up'],
        "name": kwargs['name'],
        "description": kwargs['description'],
        "vip_address": kwargs['vip_address'],
        "loadbalancer_id": kwargs['loadbalancer_id']}}
    if kwargs.get('rip_address'):
        body['lvs']['rip_address'] = kwargs['rip_address']
    if kwargs.get('subnet_id'):
        body['lvs']['subnet_id'] = kwargs['subnet_id']
    if kwargs.get('tenant_id'):
        body['lvs']['tenant_id'] = kwargs['tenant_id']
    lvs = neutronclient(
        request).create_lvs(body).get('lvs')
    return LVSPort(lvs)


def lvsport_delete(request, lvs_id):
    """LBaaS v2 Delete a given lvs port."""
    neutronclient(request).delete_lvs(lvs_id)


@memoized
def lvsport_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List lvs port that belong to a given tenant."""
    lvses = neutronclient(
        request).list_lvses(retrieve_all,
                            **kwargs).get('lvses')
    return [LVSPort(m) for m in lvses]


@memoized
def lvsport_get(request, lvs_id, **kwargs):
    """LBaaS v2 Show information of a given lvs port."""
    lvs = neutronclient(
        request).show_lvs(lvs_id,
                          **kwargs).get('lvs')
    return LVSPort(lvs)


def lvsport_update(request, lvs_id, **kwargs):
    """LBaaS v2 Update or Refresh a given lvs port."""
    body = {"lvs": {
            "admin_state_up": kwargs['admin_state_up'],
            "name": kwargs['name'],
            "description": kwargs['description']}}

    lvs = neutronclient(
        request).update_lvs(lvs_id, body).get('lvs')
    return LVSPort(lvs)
