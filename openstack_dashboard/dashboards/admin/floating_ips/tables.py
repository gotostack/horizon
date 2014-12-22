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

from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api


def get_instance_name(datum):
    return getattr(datum, "instance_name", None)


def get_instance_link(datum):
    view = "horizon:admin:instances:detail"
    if datum.instance_id:
        return urlresolvers.reverse(view, args=(datum.instance_id,))
    else:
        return None


def get_port_link(datum):
    view = "horizon:admin:networks:ports:detail"
    if datum.port_id:
        return urlresolvers.reverse(view, args=(datum.port_id,))
    else:
        return None


def get_floating_network_link(datum):
    view = "horizon:admin:networks:detail"
    if datum.floating_network_id:
        return urlresolvers.reverse(view, args=(datum.floating_network_id,))
    else:
        return None


def _get_attr(datum, attr):
    return datum.get(attr, None) if datum.get(attr, None) else ""


def get_fip_status(datum):
    return _get_attr(datum, "status")


def get_floating_network(datum):
    return _get_attr(datum, "floating_network")


class FloatingIPFilterAction(tables.FilterAction):

    def filter(self, table, fip, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [ip for ip in fip
                if q in ip.ip.lower()]


class AdminAllocateFloatingIP(tables.LinkAction):
    name = "allocate"
    verbose_name = _("Allocate Floating IP")
    url = "horizon:admin:floating_ips:allocate"
    classes = ("ajax-modal", "btn-create")


class AdminReleaseFloatingIP(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Floating IP",
            u"Delete Floating IPs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Floating IP",
            u"Deleted Floating IPs",
            count
        )

    def delete(self, request, obj_id):
        api.network.tenant_floating_ip_release(request, obj_id)


class AdminEditFloatingIP(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:admin:floating_ips:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, fip=None):
        return True if fip.get("id", None) else False


class AdminSimpleDisassociateIP(tables.BatchAction):
    name = "disassociate"
    verbose_name = _("Disassociate Floating IP")
    classes = ("btn-danger", "btn-disassociate",)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Disassociate Floating IP",
            u"Disassociate Floating IPs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Disassociate Floating IP",
            u"Disassociated Floating IPs",
            count
        )

    def allowed(self, request, fip=None):
        return True if fip.get("port_id", None) else False

    def action(self, request, obj_id):
        try:
            # Force disassociate floating ip, Ignore the port_id.
            api.network.floating_ip_disassociate(request,
                                                 floating_ip_id=obj_id)
            messages.success(request,
                             _("Successfully disassociated "
                               "floating IP: %s") % obj_id)
        except Exception:
            exceptions.handle(request,
                              _("Unable to disassociate floating IP."))


class FloatingIPsTable(tables.DataTable):
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))

    ip = tables.Column("ip",
                       link=("horizon:admin:floating_ips:detail"),
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})

    fixed_ip = tables.Column("fixed_ip_address",
                             link=get_port_link,
                             verbose_name=_("Mapped Fixed IP Address"),
                             attrs={'data-type': "ip"})

    status = tables.Column(get_fip_status,
                           verbose_name=_("Status"))

    instance = tables.Column(get_instance_name,
                             link=get_instance_link,
                             verbose_name=_("Instance"),
                             empty_value="-")

    pool = tables.Column(get_floating_network,
                         link=get_floating_network_link,
                         verbose_name=_("Pool"))

    def get_object_display(self, datum):
        return datum.ip

    def get_object_id(self, datum):
        return datum.id if datum.get("id", None) else datum.ip

    class Meta(object):
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        table_actions = (FloatingIPFilterAction,
                         AdminAllocateFloatingIP,
                         AdminReleaseFloatingIP)
        row_actions = (AdminReleaseFloatingIP,
                       AdminSimpleDisassociateIP)
