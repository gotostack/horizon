# Copyright 2012 NEC Corporation
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
from django import template
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy


LOG = logging.getLogger(__name__)


class CheckNetworkEditable(object):
    """Mixin class to determine the specified network is editable."""

    def allowed(self, request, datum=None):
        # Only administrator is allowed to create and manage shared networks.
        if datum and datum.shared:
            return False
        return True


class DeleteNetwork(policy.PolicyTargetMixin, CheckNetworkEditable,
                    tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Network",
            u"Delete Networks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Network",
            u"Deleted Networks",
            count
        )

    policy_rules = (("network", "delete_network"),)

    def delete(self, request, network_id):
        network_name = network_id
        try:
            # Retrieve the network list.
            network = api.neutron.network_get(request, network_id,
                                              expand_subnet=False)
            network_name = network.name
            LOG.debug('Network %(network_id)s has subnets: %(subnets)s',
                      {'network_id': network_id, 'subnets': network.subnets})
            for subnet_id in network.subnets:
                api.neutron.subnet_delete(request, subnet_id)
                LOG.debug('Deleted subnet %s', subnet_id)
            api.neutron.network_delete(request, network_id)
            LOG.debug('Deleted network %s successfully', network_id)
        except Exception:
            msg = _('Failed to delete network %s')
            LOG.info(msg, network_id)
            redirect = reverse("horizon:user:networks:index")
            exceptions.handle(request, msg % network_name, redirect=redirect)


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Network")
    url = "horizon:user:networks:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_network"),)


class EditNetwork(policy.PolicyTargetMixin, CheckNetworkEditable,
                  tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Network")
    url = "horizon:user:networks:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_network"),)


class CreateSubnet(policy.PolicyTargetMixin, CheckNetworkEditable,
                   tables.LinkAction):
    name = "subnet"
    verbose_name = _("Add Subnet")
    url = "horizon:user:networks:addsubnet"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_subnet"),)
    policy_target_attrs = (("network:project_id", "tenant_id"),)


def get_subnets(network):
    template_name = 'user/networks/_network_ips.html'
    context = {"subnets": network.subnets}
    return template.loader.render_to_string(template_name, context)


DISPLAY_CHOICES = (
    ("UP", pgettext_lazy("Admin state of a Network", u"UP")),
    ("DOWN", pgettext_lazy("Admin state of a Network", u"DOWN")),
)
STATUS_DISPLAY_CHOICES = (
    ("ACTIVE", pgettext_lazy("Current status of a Network", u"Active")),
    ("BUILD", pgettext_lazy("Current status of a Network", u"Build")),
    ("DOWN", pgettext_lazy("Current status of a Network", u"Down")),
    ("ERROR", pgettext_lazy("Current status of a Network", u"Error")),
)


class NetworksFilterAction(tables.FilterAction):

    def filter(self, table, networks, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [network for network in networks
                if query in network.name.lower()]


class NetworksTable(tables.DataTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link='horizon:user:networks:detail')
    subnets = tables.Column(get_subnets,
                            verbose_name=_("Subnets Associated"),)
    shared = tables.Column("shared", verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    status = tables.Column("status", verbose_name=_("Status"),
                           display_choices=STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=DISPLAY_CHOICES)

    class Meta(object):
        name = "networks"
        verbose_name = _("Networks")
        table_actions = (CreateNetwork, DeleteNetwork,
                         NetworksFilterAction)
        row_actions = (EditNetwork, CreateSubnet, DeleteNetwork)
