#    Copyright 2013, Big Switch Networks, Inc.
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

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import messages

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
    """Wrapper for neutron load balancer member."""

    def __init__(self, apiresource):
        super(Member, self).__init__(apiresource)


class Pool(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer pool."""

    def __init__(self, apiresource):
        if 'provider' not in apiresource:
            apiresource['provider'] = None
        super(Pool, self).__init__(apiresource)


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
    loadbalancer = neutronclient(
        request).create_loadbalancer(**kwargs).get('loadbalancer')
    return Loadbalancer(loadbalancer)


def loadbalancer_delete(request, loadbalancer_id):
    """LBaaS v2 Delete a given loadbalancer."""
    neutronclient(request).delete_loadbalancer(loadbalancer_id)


def loadbalancer_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List loadbalancers that belong to a given tenant."""
    loadbalancers = neutronclient(
        request).list_lbaas_loadbalancers(retrieve_all,
                                          **kwargs).get('loadbalancers')
    return [Loadbalancer(l) for l in loadbalancers]


def loadbalancer_get(request, loadbalancer_id, **kwargs):
    """LBaaS v2 Show information of a given loadbalancer."""
    loadbalancer = neutronclient(
        request).show_loadbalancer(loadbalancer_id,
                                   **kwargs).get('loadbalancer')
    return Loadbalancer(loadbalancer)


def loadbalancer_update(request, loadbalancer_id, **kwargs):
    """LBaaS v2 Update a given loadbalancer."""
    loadbalancer = neutronclient(
        request).update_loadbalancer(loadbalancer_id,
                                     **kwargs).get('loadbalancer')
    return Loadbalancer(loadbalancer)


def listener_create(request, **kwargs):
    """LBaaS v2 Create a listener."""
    listener = neutronclient(
        request).create_listener(**kwargs).get('listener')
    return Listener(listener)


def listener_delete(request, listener_id):
    """LBaaS v2 Delete a given listener."""
    neutronclient(request).delete_listener(listener_id)


def listener_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List listeners that belong to a given tenant."""
    listeners = neutronclient(
        request).list_listeners(retrieve_all,
                                **kwargs).get('listeners')
    return [Listener(l) for l in listeners]


def listener_get(request, listener_id, **kwargs):
    """LBaaS v2 Show information of a given listener."""
    listener = neutronclient(
        request).show_listener(listener_id,
                               **kwargs).get('listener')
    return Listener(listener)


def listener_update(request, listener_id, **kwargs):
    """LBaaS v2 Update a given listener."""
    listener = neutronclient(
        request).update_listener(listener_id,
                                 **kwargs).get('listener')
    return Listener(listener)


def pool_create(request, **kwargs):
    """LBaaS v2 Create a pool."""
    pool = neutronclient(
        request).create_lbaas_pool(**kwargs).get('pool')
    return Pool(pool)


def pool_delete(request, pool_id):
    """LBaaS v2 Delete a given pool."""
    neutronclient(request).delete_lbaas_pool(pool_id)


def pool_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List pools that belong to a given tenant."""
    pools = neutronclient(
        request).list_lbaas_pools(retrieve_all,
                                  **kwargs).get('pools')
    return [Pool(p) for p in pools]


def pool_get(request, pool_id, **kwargs):
    """LBaaS v2 Show information of a given pool."""
    pool = neutronclient(
        request).show_lbaas_pool(pool_id,
                                 **kwargs).get('pool')
    return Pool(pool)


def pool_update(request, pool_id, **kwargs):
    """LBaaS v2 Update a given pool."""
    pool = neutronclient(
        request).update_lbaas_pool(pool_id,
                                   **kwargs).get('pool')
    return Pool(pool)


def member_create(request, pool_id, **kwargs):
    """LBaaS v2 Create a member."""
    member = neutronclient(
        request).create_lbaas_member(pool_id,
                                     **kwargs).get('member')
    return Member(member)


def member_delete(request, member_id, pool_id):
    """LBaaS v2 Delete a given member."""
    neutronclient(request).delete_lbaas_member(member_id, pool_id)


def member_list(request, pool_id, retrieve_all=True, **kwargs):
    """LBaaS v2 List members that belong to a given tenant."""
    members = neutronclient(
        request).list_lbaas_members(pool_id,
                                    retrieve_all,
                                    **kwargs).get('members')
    return [Member(m) for m in members]


def member_get(request, member_id, pool_id, **kwargs):
    """LBaaS v2 Show information of a given member."""
    member = neutronclient(
        request).show_lbaas_member(member_id,
                                   pool_id,
                                   **kwargs).get('member')
    return Member(member)


def member_update(request, member_id, pool_id, **kwargs):
    """LBaaS v2 Update a given member."""
    member = neutronclient(
        request).update_lbaas_member(member_id,
                                     pool_id,
                                     **kwargs).get('member')
    return Member(member)


def healthmonitor_create(request, **kwargs):
    """LBaaS v2 Create a healthmonitor."""
    healthmonitor = neutronclient(
        request).create_lbaas_healthmonitor(**kwargs).get('healthmonitor')
    return Healthmonitor(healthmonitor)


def healthmonitor_delete(request, healthmonitor_id):
    """LBaaS v2 Delete a given healthmonitor."""
    neutronclient(request).delete_lbaas_healthmonitor(healthmonitor_id)


def healthmonitor_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List healthmonitors that belong to a given tenant."""
    healthmonitors = neutronclient(
        request).list_lbaas_healthmonitors(retrieve_all,
                                           **kwargs).get('healthmonitors')
    return [Healthmonitor(h) for h in healthmonitors]


def healthmonitor_get(request, healthmonitor_id, **kwargs):
    """LBaaS v2 Show information of a given healthmonitor."""
    healthmonitor = neutronclient(
        request).show_lbaas_healthmonitor(healthmonitor_id,
                                          **kwargs).get('healthmonitor')
    return Healthmonitor(healthmonitor)


def healthmonitor_update(request, healthmonitor_id, **kwargs):
    """LBaaS v2 Update a given healthmonitor."""
    healthmonitor = neutronclient(
        request).update_lbaas_healthmonitor(healthmonitor_id,
                                            **kwargs).get('healthmonitor')
    return Healthmonitor(healthmonitor)


def acl_create(request, **kwargs):
    """LBaaS v2 Create an acl."""
    acl = neutronclient(
        request).create_acl(**kwargs).get('acl')
    return Acl(acl)


def acl_delete(request, acl_id):
    """LBaaS v2 Delete a given acl."""
    neutronclient(request).delete_acl(acl_id)


def acl_list(request, retrieve_all=True, **kwargs):
    """LBaaS v2 List acls that belong to a given tenant."""
    acls = neutronclient(
        request).list_acls(retrieve_all,
                           **kwargs).get('acls')
    return [Acl(a) for a in acls]


def acl_get(request, acl_id, **kwargs):
    """LBaaS v2 Show information of a given acl."""
    acl = neutronclient(
        request).show_acl(acl_id,
                          **kwargs).get('acl')
    return Acl(acl)


def acl_update(request, acl_id, **kwargs):
    """LBaaS v2 Update a given acl."""
    acl = neutronclient(
        request).update_acl(acl_id,
                            **kwargs).get('acl')
    return Acl(acl)
