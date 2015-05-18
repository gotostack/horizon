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
from django.utils.http import urlencode
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

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


class AddListenerLink(tables.LinkAction):
    name = "addlistener"
    verbose_name = _("Add Listener")
    url = "horizon:user:loadbalancers:addlistener"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_listener"),)

    def get_link_url(self, datum=None):
        if datum:
            base_url = reverse(self.url)
            params = urlencode({"loadbalancer_id": datum.id})
            return "?".join([base_url, params])
        return reverse(self.url)


STATUS_CHOICES = (
    ("Active", True),
    ("Down", True),
    ("Error", False),
)


STATUS_DISPLAY_CHOICES = (
    ("Active", pgettext_lazy("Current status of a Pool",
                             u"Active")),
    ("Down", pgettext_lazy("Current status of a Pool",
                           u"Down")),
    ("Error", pgettext_lazy("Current status of a Pool",
                            u"Error")),
    ("Created", pgettext_lazy("Current status of a Pool",
                              u"Created")),
    ("Pending_Create", pgettext_lazy("Current status of a Pool",
                                     u"Pending Create")),
    ("Pending_Update", pgettext_lazy("Current status of a Pool",
                                     u"Pending Update")),
    ("Pending_Delete", pgettext_lazy("Current status of a Pool",
                                     u"Pending Delete")),
    ("Inactive", pgettext_lazy("Current status of a Pool",
                               u"Inactive")),
)


class ViewLoadbalancerStatuses(tables.LinkAction):
    name = "view"
    verbose_name = _("View Details")
    url = "horizon:user:loadbalancers:loadbalancerstatuses"
    classes = ("ajax-modal", "btn-view")

    def get_link_url(self, datum=None):
        obj_id = self.table.get_object_id(datum)
        return reverse(self.url, args=(obj_id,))


class LoadbalancerTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:user:loadbalancers:loadbalancerdetails")
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
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    class Meta(object):
        name = "loadbalancers"
        verbose_name = _("Loadbalancers")
        status_columns = ["status"]
        row_class = UpdateLoadbalancersRow
        table_actions = (NameFilterAction, AddLoadbalancerLink,
                         DeleteLoadbalancer)
        row_actions = (ViewLoadbalancerStatuses,
                       UpdateLoadbalancerLink,
                       AddListenerLink,
                       DeleteLoadbalancer)


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
                loadbalancer = api.lbaas_v2.loadbalancer_get(
                    request, listener.loadbalancer_id)
                listener.loadbalancer_name = loadbalancer.name
            except Exception:
                listener.loadbalancer_name = listener.loadbalancer_id
        return listener


class AddAclToListenerLink(tables.LinkAction):
    name = "addacltolistener"
    verbose_name = _("Add Acl")
    url = "horizon:user:loadbalancers:addacl"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_acl"),)

    def get_link_url(self, datum=None):
        if datum:
            return reverse(self.url, args=(datum.id,))


class AddPoolLink(tables.LinkAction):
    name = "addpool"
    verbose_name = _("Add Pool")
    url = "horizon:user:loadbalancers:addpool"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_pool"),)

    def get_link_url(self, datum):
        if datum:
            base_url = reverse(self.url)
            params = urlencode({"listener_id": datum.id,
                                "protocol": datum.protocol})
            return "?".join([base_url, params])
        return reverse(self.url)


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
        row_actions = (UpdateListenerLink,
                       AddPoolLink,
                       AddAclToListenerLink,
                       DeleteListener)


class DeletePool(tables.DeleteAction):
    name = "deletepool"
    policy_rules = (("network", "delete_pool"),)
    help_text = _("Deleted pools are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Pool",
            u"Delete Pools",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Pool",
            u"Scheduled deletion of Pools",
            count
        )

    def delete(self, request, obj_id):
        api.lbaas_v2.pool_delete(request, obj_id)


class UpdatePoolLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatepool"
    verbose_name = _("Edit Pool")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_pool"),)

    def get_link_url(self, pool):
        base_url = reverse("horizon:user:loadbalancers:updatepool",
                           kwargs={'pool_id': pool.id})
        return base_url


class UpdatePoolsRow(tables.Row):
    ajax = True

    def get_data(self, request, pool_id):
        return api.lbaas_v2.pool_get(request, pool_id)


class AddMemberToPoolLink(tables.LinkAction):
    name = "addmembertopool"
    verbose_name = _("Add Member")
    url = "horizon:user:loadbalancers:addmember"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_member"),)

    def get_link_url(self, datum=None):
        if datum:
            return reverse(self.url, args=(datum.id,))


class AddHealthmonitorLink(tables.LinkAction):
    name = "addhealthmonitor"
    verbose_name = _("Add Healthmonitor")
    url = "horizon:user:loadbalancers:addhealthmonitor"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_healthmonitor"),)

    def get_link_url(self, datum=None):
        if datum:
            base_url = reverse(self.url)
            params = urlencode({"pool_id": datum.id})
            return "?".join([base_url, params])
        return reverse(self.url)


class AddPool(tables.LinkAction):
    name = "addpool"
    verbose_name = _("Add Pool")
    url = "horizon:user:loadbalancers:addpool"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_pool"),)


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
        table_actions = (NameFilterAction, AddPool,
                         DeletePool)
        row_actions = (UpdatePoolLink,
                       AddMemberToPoolLink,
                       AddHealthmonitorLink,
                       DeletePool)


class MemberFilterAction(tables.FilterAction):

    def filter(self, table, objects, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [o for o in objects
                if query in o.address.lower()]


class AddMemberLink(tables.LinkAction):
    name = "addmember"
    verbose_name = _("Add Member")
    url = "horizon:user:loadbalancers:addmember"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_member"),)

    def get_link_url(self, datum=None):
        pool_id = self.table.kwargs['pool_id']
        return reverse(self.url, args=(pool_id,))


class DeleteMember(tables.DeleteAction):
    name = "deletemember"
    policy_rules = (("network", "delete_member"),)
    help_text = _("Deleted members are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Member",
            u"Delete Members",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Member",
            u"Scheduled deletion of Members",
            count
        )

    def delete(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.lbaas_v2.member_delete(request,
                                   obj_id,
                                   datum.pool_id)


class UpdateMemberLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatemember"
    verbose_name = _("Edit Member")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_member"),)

    def get_link_url(self, member):
        base_url = reverse("horizon:user:loadbalancers:updatemember",
                           kwargs={'pool_id': member.pool_id,
                                   'member_id': member.id})
        return base_url


class UpdateMembersRow(tables.Row):
    ajax = True

    def get_data(self, request, member_id):
        return api.lbaas_v2.member_get(request, member_id)


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
        table_actions = (MemberFilterAction, AddMemberLink,
                         DeleteMember)
        row_actions = (UpdateMemberLink, DeleteMember)


class AddAclLink(tables.LinkAction):
    name = "addacl"
    verbose_name = _("Add Acl")
    url = "horizon:user:loadbalancers:addacl"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_acl"),)

    def get_link_url(self, datum=None):
        listener_id = self.table.kwargs['listener_id']
        return reverse(self.url, args=(listener_id,))


class DeleteAcl(tables.DeleteAction):
    name = "deleteacl"
    policy_rules = (("network", "delete_acl"),)
    help_text = _("Deleted acls are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Acl",
            u"Delete Acls",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Acl",
            u"Scheduled deletion of Acls",
            count
        )

    def delete(self, request, obj_id):
        api.lbaas_v2.acl_delete(request, obj_id)


class UpdateAclLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updateacl"
    verbose_name = _("Edit Acl")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_acl"),)

    def get_link_url(self, acl):
        base_url = reverse("horizon:user:loadbalancers:updateacl",
                           kwargs={'listener_id': acl.listener_id,
                                   'acl_id': acl.id})
        return base_url


class UpdateAclsRow(tables.Row):
    ajax = True

    def get_data(self, request, acl_id):
        acl = api.lbaas_v2.acl_get(request, acl_id)
        return acl


class AclsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    acl_type = tables.Column('acl_type', verbose_name=_("ACL Type"))
    description = tables.Column('description', verbose_name=_("Description"))
    listener_id = tables.Column('listener_id', verbose_name=_("Listener"))
    action = tables.Column('action', verbose_name=_("Action"))
    condition = tables.Column('condition', verbose_name=_("Condition"))
    operator = tables.Column('operator', verbose_name=_("Operator"))
    match = tables.Column('match', verbose_name=_("Match"))
    match_condition = tables.Column('match_condition',
                                    verbose_name=_("Match Condition"))
    admin_state_up = tables.Column('admin_state_up',
                                   verbose_name=_("Admin State"))

    class Meta(object):
        name = "acls"
        verbose_name = _("ACLs")
        table_actions = (NameFilterAction, AddAclLink,
                         DeleteAcl)
        row_actions = (UpdateAclLink, DeleteAcl)


class HealthmonitorFilterAction(tables.FilterAction):

    def filter(self, table, objects, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [o for o in objects
                if query in o.type.lower()]


class DeleteHealthmonitor(tables.DeleteAction):
    name = "deletehealthmonitor"
    policy_rules = (("network", "delete_healthmonitor"),)
    help_text = _("Deleted healthmonitors are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Healthmonitor",
            u"Delete Healthmonitors",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Healthmonitor",
            u"Scheduled deletion of Healthmonitors",
            count
        )

    def delete(self, request, obj_id):
        api.lbaas_v2.healthmonitor_delete(request,
                                          obj_id)


class UpdateHealthmonitorLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatehealthmonitor"
    verbose_name = _("Edit Healthmonitor")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_healthmonitor"),)

    def get_link_url(self, healthmonitor):
        base_url = reverse("horizon:user:loadbalancers:updatehealthmonitor",
                           kwargs={'healthmonitor_id': healthmonitor.id})
        return base_url


class UpdateHealthmonitorRow(tables.Row):
    ajax = True

    def get_data(self, request, healthmonitor_id):
        return api.lbaas_v2.healthmonitor_get(request, healthmonitor_id)


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
        table_actions = (NameFilterAction, AddHealthmonitorLink,
                         DeleteHealthmonitor)
        row_actions = (UpdateHealthmonitorLink, DeleteHealthmonitor)


class AddRedundanceLink(tables.LinkAction):
    name = "addredundance"
    verbose_name = _("Add Redundance")
    url = "horizon:user:loadbalancers:addredundance"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_redundance"),)

    def get_link_url(self, datum=None):
        loadbalancer_id = self.table.kwargs['loadbalancer_id']
        return reverse(self.url, args=(loadbalancer_id,))


class DeleteRedundance(tables.DeleteAction):
    name = "deleteredundance"
    policy_rules = (("network", "delete_redundance"),)
    help_text = _("Deleted redundances are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Redundance",
            u"Delete Redundances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Redundance",
            u"Scheduled deletion of Redundances",
            count
        )

    def delete(self, request, obj_id):
        loadbalancer_id = self.table.kwargs['loadbalancer_id']
        api.lbaas_v2.redundance_delete(request,
                                       obj_id,
                                       loadbalancer_id)


class UpdateRedundanceLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updateredundance"
    verbose_name = _("Edit Redundance")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_redundance"),)

    def get_link_url(self, redundance):
        loadbalancer_id = self.table.kwargs['loadbalancer_id']
        base_url = reverse("horizon:user:loadbalancers:updateredundance",
                           kwargs={
                               'loadbalancer_id': loadbalancer_id,
                               'redundance_id': redundance.id})
        return base_url


class UpdateLbRedundancesRow(tables.Row):
    ajax = True

    def get_data(self, request, lbr_id):
        loadbalancer_id = self.table.kwargs['loadbalancer_id']
        lbredundance = api.lbaas_v2.redundance_get(request,
                                                   lbr_id,
                                                   loadbalancer_id)
        return lbredundance


class LbRedundancesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    vip_address = tables.Column('vip_address',
                                verbose_name=_("IP Address"),
                                attrs={'data-type': "ip"})
    description = tables.Column('description', verbose_name=_("Description"))
    admin_state_up = tables.Column('admin_state_up',
                                   verbose_name=_("Admin State"))
    status = tables.Column('provisioning_status',
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    agent_id = tables.Column('agent_id',
                             verbose_name=_("Agent"))

    class Meta(object):
        name = "lbredundances"
        verbose_name = _("Loadbalancer Redundances")
        status_columns = ["status"]
        row_class = UpdateLbRedundancesRow
        table_actions = (NameFilterAction, AddRedundanceLink,
                         DeleteRedundance)
        row_actions = (UpdateRedundanceLink, DeleteRedundance)
