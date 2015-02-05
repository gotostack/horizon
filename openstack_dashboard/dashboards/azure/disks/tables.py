# Copyright 2015 Letv Cloud Computing
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

from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class FilterAction(tables.FilterAction):

    def filter(self, table, items, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [i for i in items
                if q in i.name.lower()]


def get_attached_to(disk):
    if getattr(disk, 'attached_to') is not None:
        return getattr(disk, 'attached_to').role_name
    return 'N/A'


class DeleteDisk(tables.DeleteAction):
    help_text = _("Deleted disks are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Disk",
            u"Delete Disks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Disk",
            u"Deleted Disks",
            count
        )

    def allowed(self, request, disk=None):
        if disk and disk.attached_to is not None:
            return False
        return True

    def delete(self, request, obj_id):
        api.azure_api.disk_delete(request, obj_id, True)


def get_detail_link(datum):
    url = "horizon:azure:disks:detail"
    return urlresolvers.reverse(url, args=[datum.name])


class DisksTable(tables.DataTable):
    name = tables.Column("name",
                         link=get_detail_link,
                         verbose_name=_("Name"))
    logical_disk_size_in_gb = tables.Column("logical_disk_size_in_gb",
                                            verbose_name=_("Size (GB)"))
    os = tables.Column("os",
                       verbose_name=_("Operating system"))
    location = tables.Column("location",
                             verbose_name=_("Location"))
    attached_to = tables.Column(get_attached_to,
                                verbose_name=_("Virtual Machine Attached To"))

    class Meta:
        name = 'disks'
        verbose_name = _('Disks')
        table_actions = (FilterAction, DeleteDisk)
        row_actions = (DeleteDisk, )

    def get_object_id(self, datum):
        return datum.name
