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

from django.core.urlresolvers import reverse
from django.http import HttpResponse  # noqa
from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.templatetags import sizeformat

LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)
VOLUME_ATTACH_READY_STATES = ("ACTIVE", "SHUTOFF")
SNAPSHOT_READY_STATES = ("ACTIVE", "SHUTOFF", "PAUSED", "SUSPENDED")

POWER_STATES = {
    0: "NO STATE",
    1: "RUNNING",
    2: "BLOCKED",
    3: "PAUSED",
    4: "SHUTDOWN",
    5: "SHUTOFF",
    6: "CRASHED",
    7: "SUSPENDED",
    8: "FAILED",
    9: "BUILDING",
}

PAUSE = 0
UNPAUSE = 1
SUSPEND = 0
RESUME = 1


def get_ips(instance):
    template_name = 'azure/instances/_instance_ips.html'
    context = {"instance": instance}
    return template.loader.render_to_string(template_name, context)


def get_size(instance):
    if hasattr(instance, "role"):
        template_name = 'azure/instances/_instance_flavor.html'
        size_ram = sizeformat.mb_float_format(instance.role.memory_in_mb)
        size_disk = sizeformat.diskgbformat(
            instance.role.virtual_machine_resource_disk_size_in_mb)
        context = {
            "name": instance.role.name,
            "id": instance.role_name,
            "size_disk": size_disk,
            "size_ram": size_ram,
            "vcpus": instance.role.cores
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")


class DetailLink(tables.LinkAction):
    name = "detail"
    verbose_name = _("View Detail")
    url = "horizon:azure:instances:detail"

    def get_link_url(self, datum):
        return reverse(self.url, args=(datum.cloud_service_name,
                                       datum.deployment_name,
                                       datum.role_name))


def get_detail_link(datum):
    url = "horizon:azure:instances:detail"
    return reverse(url, args=(datum.cloud_service_name,
                              datum.deployment_name,
                              datum.instance_name))


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:azure:instances:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    ajax = True

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(LaunchLink, self).__init__(attrs, **kwargs)

    def single(self, table, request, object_id=None):
        self.allowed(request, None)
        return HttpResponse(self.render())


class InstanceFilterAction(tables.FilterAction):

    def filter(self, table, users, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [u for u in users
                if q in u.name.lower()]


class InstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )

    STATUS_CHOICES = (
        ("Starting", True),
        ("Started", True),
        ("Stopping", True),
        ("Stopped", True),
        ("Unknown", False),
        ("rescue", True),
        ("shelved_offloaded", True),
    )
    name = tables.Column("instance_name",
                         link=get_detail_link,
                         verbose_name=_("Instance Name"))
    ip = tables.Column(get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column("power_state",
                           status=True,
                           verbose_name=_("PowerState"))
    dns_url = tables.Column("dns_url",
                            verbose_name=_("SSH"))

    def get_object_id(self, datum):
        return (datum.instance_name
                if hasattr(datum, 'instance_name') else datum.role_name)

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        # status_columns = ["status", "task"]
        table_actions = (InstanceFilterAction,
                         LaunchLink)
        row_actions = (DetailLink, )
