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
from django.template import defaultfilters as filters
from django.utils import http
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class NameFilterAction(tables.FilterAction):

    def filter(self, table, objects, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [o for o in objects
                if query in o.name.lower()]


class AddLoadbalancerLink(tables.LinkAction):
    name = "addloadbalancer"
    verbose_name = _("Add Loadbalancer")
    url = "horizon:user:loadbalancers:addloadbalancer"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_loadbalancer"),)


class DeleteLoadbalancer(tables.DeleteAction):
    name = "deleteloadbalancer"
    policy_rules = (("network", "delete_loadbalancer"),)
    help_text = _("Deleted loadbalancers are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Loadbalancer",
            u"Delete Loadbalancers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Loadbalancer",
            u"Scheduled deletion of Loadbalancers",
            count
        )

    def delete(self, request, obj_id):
        api.lbaas_v2.loadbalancer_delete(request, obj_id)


class UpdateLoadbalancerLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updateloadbalancer"
    verbose_name = _("Edit Loadbalancer")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_loadbalancer"),)

    def get_link_url(self, loadbalancer):
        base_url = reverse("horizon:user:loadbalancers:updateloadbalancer",
                           kwargs={'loadbalancer_id': loadbalancer.id})
        return base_url


class UpdateLoadbalancersRow(tables.Row):
    ajax = True

    def get_data(self, request, loadbalancer_id):
        loadbalancer = api.lbaas_v2.loadbalancer_get(request, loadbalancer_id)
        try:
            subnet = api.neutron.subnet_get(request,
                                            loadbalancer.vip_subnet_id)
            loadbalancer.subnet_name = subnet.cidr
        except Exception:
            loadbalancer.subnet_name = loadbalancer.subnet_id
        return loadbalancer


class LoadbalancerTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:user:loadbalancers:detail")
    description = tables.Column('description', verbose_name=_("Description"))
    provider = tables.Column(
        'provider', verbose_name=_("Provider"),
        filters=(lambda v: filters.default(v, _('N/A')),))
    vip_address = tables.Column('vip_address',
                                verbose_name=_("IP Address"),
                                attrs={'data-type': "ip"})
    subnet_name = tables.Column('subnet_name', verbose_name=_("Subnet"))
    status = tables.Column('provisioning_status',
                           verbose_name=_("Status"),
                           status=True)

    class Meta(object):
        name = "loadbalancers"
        verbose_name = _("Loadbalancers")
        status_columns = ["status"]
        row_class = UpdateLoadbalancersRow
        table_actions = (NameFilterAction, AddLoadbalancerLink,
                         DeleteLoadbalancer)
        row_actions = (UpdateLoadbalancerLink, DeleteLoadbalancer)


class AddListenerLink(tables.LinkAction):
    name = "addlistener"
    verbose_name = _("Add Listener")
    url = "horizon:user:loadbalancers:addlistener"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_listener"),)


class DeleteListener(tables.DeleteAction):
    name = "deletelistener"
    policy_rules = (("network", "delete_listener"),)
    help_text = _("Deleted listeners are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Listener",
            u"Delete Listeners",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Listener",
            u"Scheduled deletion of Listeners",
            count
        )

    def delete(self, request, obj_id):
        api.lbaas_v2.listener_delete(request, obj_id)


class UpdateListenerLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatelistener"
    verbose_name = _("Edit Listener")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_listener"),)

    def get_link_url(self, listener):
        base_url = reverse("horizon:user:loadbalancers:updatelistener",
                           kwargs={'listener_id': listener.id})
        return base_url


class UpdateListenersRow(tables.Row):
    ajax = True

    def get_data(self, request, listener_id):
        listener = api.lbaas_v2.listener_get(request, listener_id)
        if listener.default_pool_id:
            try:
                pool = api.lbaas_v2.pool_get(request,
                                             listener.default_pool_id)
                listener.pool_name = pool.name
            except Exception:
                listener.pool_name = listener.default_pool_id
            try:
                loadbalancer = api.lbaas_v2.loadbalancer_get(request,
                                                             listener.loadbalancer_id)
                listener.loadbalancer_name = loadbalancer.name
            except Exception:
                listener.loadbalancer_name = listener.loadbalancer_id
        return loadbalancer


class ListenersTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:user:loadbalancers:listenerdetails")
    description = tables.Column('description', verbose_name=_("Description"))
    protocol = tables.Column('protocol',
                            verbose_name=_("Protocol"))
    protocol_port = tables.Column('protocol_port',
                                  verbose_name=_("Protocol Port"))
    connection_limit = tables.Column('connection_limit',
                                     verbose_name=_("Connection Limit"))
    loadbalancer_name = tables.Column('loadbalancer_name',
                                      verbose_name=_("Loadbalancer"))
    pool_name = tables.Column('pool_name',
                              verbose_name=_("Pool"))

    class Meta(object):
        name = "listeners"
        verbose_name = _("Listeners")
        row_class = UpdateListenersRow
        table_actions = (NameFilterAction, AddListenerLink,
                         DeleteListener)
        row_actions = (UpdateListenerLink, DeleteListener)


class PoolsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:user:loadbalancers:pooldetails")
    description = tables.Column('description', verbose_name=_("Description"))
    protocol = tables.Column('protocol', verbose_name=_("Protocol"))
    lb_algorithm = tables.Column('lb_algorithm',
                                 verbose_name=_("Algorithm"))
    healthmonitor_id = tables.Column('healthmonitor_id',
                                     verbose_name=_("Healthmonitor"))

    class Meta(object):
        name = "pools"
        verbose_name = _("Pools")
        table_actions = (NameFilterAction,)


class MemberFilterAction(tables.FilterAction):

    def filter(self, table, objects, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [o for o in objects
                if query in o.address.lower()]


class MembersTable(tables.DataTable):
    address = tables.Column('address',
                            verbose_name=_("IP Address"),
                            attrs={'data-type': "ip"})
    protocol_port = tables.Column('protocol_port',
                                  verbose_name=_("Protocol Port"))
    weight = tables.Column('weight',
                           verbose_name=_("Weight"))

    class Meta(object):
        name = "members"
        verbose_name = _("Members")
        table_actions = (MemberFilterAction,)


class AclsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    acl_type = tables.Column('acl_type', verbose_name=_("Acl Type"))
    description = tables.Column('description', verbose_name=_("Description"))
    listener_id = tables.Column('listener_id', verbose_name=_("Listener"))
    action = tables.Column('action', verbose_name=_("Action"))
    condition = tables.Column('condition', verbose_name=_("Condition"))
    operator = tables.Column('operator', verbose_name=_("Operator"))
    match = tables.Column('match', verbose_name=_("Match"))
    match_condition = tables.Column('match_condition',
                                    verbose_name=_("Match Condition"))

    class Meta(object):
        name = "acls"
        verbose_name = _("Acls")
        table_actions = (NameFilterAction,)


class HealthmonitorFilterAction(tables.FilterAction):

    def filter(self, table, objects, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [o for o in objects
                if query in o.type.lower()]


class HealthmonitorsTable(tables.DataTable):
    monitor_type = tables.Column(
        "type", verbose_name=_("Monitor Type"))
    delay = tables.Column("delay", verbose_name=_("Delay"))
    timeout = tables.Column("timeout", verbose_name=_("Timeout"))
    max_retries = tables.Column("max_retries", verbose_name=_("Max Retries"))
    http_method = tables.Column("http_method", verbose_name=_("Http Method"))
    url_path = tables.Column("url_path", verbose_name=_("Url Path"))
    expected_codes = tables.Column("expected_codes",
                                   verbose_name=_("Expected Codes"))

    class Meta(object):
        name = "healthmonitors"
        verbose_name = _("Healthmonitors")
        table_actions = (HealthmonitorFilterAction,)
