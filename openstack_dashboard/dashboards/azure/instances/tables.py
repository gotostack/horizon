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
from django.http import HttpResponse  # noqa
from django import template
from django.utils.http import urlencode
from django.utils.translation import npgettext_lazy
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from horizon.templatetags import sizeformat

from openstack_dashboard import api
from openstack_dashboard.dashboards.azure.instances.workflows \
    import resize_instance
from openstack_dashboard.dashboards.azure.instances.workflows \
    import update_instance

LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("Started", "Starting", "Suspended")
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
    if hasattr(instance, "role_size"):
        template_name = 'azure/instances/_instance_flavor.html'
        size_ram = sizeformat.mb_float_format(instance.role_size.memory_in_mb)
        size_disk = sizeformat.diskgbformat(
            instance.role_size.virtual_machine_resource_disk_size_in_mb)
        context = {
            "name": instance.role_size.name,
            "id": instance.role_name,
            "size_disk": size_disk,
            "size_ram": size_ram,
            "vcpus": instance.role_size.cores
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")


class DetailLink(tables.LinkAction):
    name = "detail"
    verbose_name = _("View Detail")
    url = "horizon:azure:instances:detail"

    def get_link_url(self, datum):
        return urlresolvers.reverse(self.url,
                                    args=(datum.cloud_service_name,
                                          datum.deployment_name,
                                          datum.role_name))


def get_detail_link(datum):
    url = "horizon:azure:instances:detail"
    return urlresolvers.reverse(url,
                                args=(datum.cloud_service_name,
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


class FilterAction(tables.FilterAction):

    def filter(self, table, items, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [i for i in items
                if q in i.name.lower()]


class TerminateInstance(tables.BatchAction):
    name = "terminate"
    classes = ("btn-danger",)
    icon = "off"
    help_text = _("The instance will be deleted, "
                  "disks associated with the instance"
                  " are still in the disk repository.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Terminate Instance",
            u"Terminate Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled termination of Instance",
            u"Scheduled termination of Instances",
            count
        )

    def action(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        cs = api.azure_api.cloud_service_detail(
            request,
            datum.cloud_service_name,
            True)

        # In this azure dashboard, all cloud service has only one deployment
        if len(cs.deployments[0].role_list) <= 1:
            # If the instance is the last one of
            # this cloudservice/deployment,
            # just delete the deployment directly.
            api.azure_api.deployment_delete(
                request,
                datum.cloud_service_name,
                # If instance was created from horizon,
                # the deployment name was same as cloud_service_name.
                datum.cloud_service_name)
            # Can not delete the cloud service here because
            # delete deployment request just return 202 (Accepted).
            # If here delete the cloud service immediately,
            # it will cause a 409 (Conflict) error.
            # Why 409 ? Because the delete deployment request was not
            # completely finished.
            # TODO(Yulong) delete the cloud service
            # api.azure_api.cloud_service_delete(request,
            #                                   datum.cloud_service_name)
        else:
            api.azure_api.virtual_machine_delete(
                request,
                datum.cloud_service_name,
                # If instance was created from horizon,
                # the deployment name was same as cloud_service_name.
                datum.cloud_service_name,
                obj_id)


class StartInstance(tables.BatchAction):
    name = "start"
    classes = ('btn-confirm',)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Start Instance",
            u"Start Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Started Instance",
            u"Started Instances",
            count
        )

    def allowed(self, request, instance):
        return ((instance is None) or
                (instance.power_state in ("Stopped", "Suspended")))

    def action(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.azure_api.virtual_machine_start(request,
                                            datum.cloud_service_name,
                                            datum.cloud_service_name,
                                            obj_id)


class RestartInstance(tables.BatchAction):
    name = "reboot"
    classes = ('btn-danger', 'btn-reboot')

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Restart Instance",
            u"Restart Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Restart Instance",
            u"Restart Instances",
            count
        )

    def allowed(self, request, instance=None):
        if instance is not None:
            return ((instance.power_state == 'Started')
                    and instance.power_state.lower() != "deleting")
        else:
            return True

    def action(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.azure_api.virtual_machine_restart(request,
                                              datum.cloud_service_name,
                                              datum.cloud_service_name,
                                              obj_id)


class StopInstance(tables.BatchAction):
    name = "stop"
    classes = ('btn-danger',)

    @staticmethod
    def action_present(count):
        return npgettext_lazy(
            "Action to perform (the instance is currently running)",
            u"Shut Off Instance",
            u"Shut Off Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return npgettext_lazy(
            "Past action (the instance is currently already Shut Off)",
            u"Shut Off Instance",
            u"Shut Off Instances",
            count
        )

    def allowed(self, request, instance):
        return ((instance is None)
                or ((instance.power_state in ACTIVE_STATES)
                    and instance.power_state.lower() != "deleting"))

    def action(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.azure_api.virtual_machine_shutdown(request,
                                               datum.cloud_service_name,
                                               datum.cloud_service_name,
                                               obj_id)


class ResizeLink(tables.LinkAction):
    name = "resize"
    verbose_name = _("Resize Instance")
    url = "horizon:azure:instances:resize"
    classes = ("ajax-modal", "btn-danger")

    def get_link_url(self, project):
        return self._get_link_url(project, 'flavor_choice')

    def _get_link_url(self, project, step_slug):
        base_url = urlresolvers.reverse(
            self.url,
            args=[project.cloud_service_name,
                  project.deployment_name,
                  project.role_name])
        next_url = self.table.get_full_url()
        params = {"step": step_slug,
                  resize_instance.ResizeInstance.redirect_param_name: next_url}
        param = urlencode(params)
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        return ((instance.power_state in ACTIVE_STATES)
                and instance.power_state.lower() != "deleting")


class EditInstance(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Instance")
    url = "horizon:azure:instances:update"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, project):
        return self._get_link_url(project, 'instance_info')

    def _get_link_url(self, project, step_slug):
        base_url = urlresolvers.reverse(
            self.url,
            args=[project.cloud_service_name,
                  project.deployment_name,
                  project.role_name])
        next_url = self.table.get_full_url()
        params = {"step": step_slug,
                  update_instance.UpdateInstance.redirect_param_name: next_url}
        param = urlencode(params)
        return "?".join([base_url, param])

    def allowed(self, request, instance):
        return ((instance.power_state in ACTIVE_STATES)
                and instance.power_state.lower() != "deleting")


class AddEndpoint(tables.LinkAction):
    name = "addendpoint"
    verbose_name = _("Add Endpoint")
    classes = ("btn-rebuild", "ajax-modal")
    url = "horizon:azure:instances:addendpoint"

    def allowed(self, request, instance=None):
        return ((instance.power_state in ACTIVE_STATES)
                and instance.power_state.lower() != "deleting")

    def get_link_url(self, datum):
        return urlresolvers.reverse(
            self.url,
            args=[datum.cloud_service_name,
                  datum.deployment_name,
                  datum.role_name])


class RemoveEndpoint(AddEndpoint):
    name = "removeendpoint"
    verbose_name = _("Remove Endpoint")
    url = "horizon:azure:instances:removeendpoint"


class AttachDataDisk(AddEndpoint):
    name = "attachdatadisk"
    verbose_name = _("Attach Data Disk")
    url = "horizon:azure:instances:attach"

    def allowed(self, request, instance=None):
        return ((instance.power_state in ACTIVE_STATES)
                and instance.power_state.lower() != "deleting"
                and len(instance.role.data_virtual_hard_disks) == 0)


class DeattachDataDisk(tables.BatchAction):
    name = "de-attach"
    verbose_name = _("De-attach Data Disk")
    classes = ('btn-danger',)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"De-attach Instance",
            u"De-attach Instances",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"De-attached Instance",
            u"De-attached Instances",
            count
        )

    def allowed(self, request, instance=None):
        return ((instance.power_state == 'Started')
                and instance.power_state.lower() != "deleting"
                and len(instance.role.data_virtual_hard_disks) > 0)

    def action(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.azure_api.data_disk_deattach(request,
                                         datum.cloud_service_name,
                                         datum.cloud_service_name,
                                         obj_id)


STATUS_DISPLAY_CHOICES = (
    ("Started", pgettext_lazy("Current status of an Instance", u"Started")),
    ("Suspended", pgettext_lazy("Current status of an Instance",
                                u"Suspended")),
    ("RunningTransitioning", pgettext_lazy("Current status of an Instance",
                                           u"RunningTransitioning")),
    ("SuspendedTransitioning", pgettext_lazy(
        "Current status of an Instance", u"SuspendedTransitioning")),
    ("Starting", pgettext_lazy("Current status of an Instance", u"Starting")),
    ("Suspending", pgettext_lazy("Current status of an Instance",
                                 u"Suspending")),
    ("Deploying", pgettext_lazy("Current status of an Instance",
                                u"Deploying")),
    ("Deleting", pgettext_lazy("Current status of an Instance", u"Deleting")),
)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        datum = self.table.get_object_by_id(instance_id)
        try:
            instance = api.azure_api.virtual_machine_get(
                request,
                datum.cloud_service_name,
                datum.deployment_name,
                instance_id)
            cloudservices = api.azure_api.cloud_service_detail(
                request,
                datum.cloud_service_name,
                True)
            status = api.azure_api.get_role_instance_status(
                cloudservices.deployments[0], instance_id)
            instance.power_state = status
            instance.role_size = datum.role_size
            instance.cloud_service_name = datum.cloud_service_name
            instance.deployment_name = datum.deployment_name
            instance.role = datum.role
        except Exception:
            instance = datum
            exceptions.handle(request,
                              _('Unable to retrieve'
                                ' instance "%s" detail.') % instance_id,
                              ignore=True)
        return instance


class InstancesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Started", True),
        ("Suspended", True),
        ("RunningTransitioning", True),
        ("SuspendedTransitioning", True),
        ("Starting", True),
        ("Suspending", True),
        ("Deploying", True),
        ("Deleting", True),
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
    instance_status = tables.Column("instance_status",
                                    verbose_name=_("Instance Status"),
                                    status=True)
    power_state = tables.Column("power_state",
                                status=True,
                                verbose_name=_("Power State"),
                                status_choices=STATUS_CHOICES,
                                display_choices=STATUS_DISPLAY_CHOICES)
    cloud_service_name = tables.Column("cloud_service_name",
                                       verbose_name=_("Cloud Service"))
    dns_url = tables.Column("dns_url",
                            verbose_name=_("DNS"))

    def get_object_display(self, datum):
        return (datum.instance_name
                if hasattr(datum, 'instance_name') else datum.role_name)

    def get_object_id(self, datum):
        return (datum.instance_name
                if hasattr(datum, 'instance_name') else datum.role_name)

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        status_columns = ["power_state", ]
        row_class = UpdateRow
        table_actions_menu = (StartInstance, StopInstance)
        table_actions = (FilterAction, LaunchLink, TerminateInstance)
        row_actions = (DetailLink, TerminateInstance,
                       StartInstance, StopInstance,
                       RestartInstance, ResizeLink,
                       EditInstance,
                       AddEndpoint, RemoveEndpoint,
                       AttachDataDisk, DeattachDataDisk)


class EndpointsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    protocol = tables.Column("protocol",
                             verbose_name=_("Protocol"))
    port = tables.Column("port",
                         verbose_name=_("Port (Cloud Service Public)"))
    local_port = tables.Column("local_port",
                               verbose_name=_("Local Port"))
    load_balanced_endpoint_set_name = tables.Column(
        "load_balanced_endpoint_set_name",
        verbose_name=_("load balanced endpoint set name"))

    class Meta:
        name = 'instance_endpoints'
        verbose_name = _('Instance Endpoints')
        table_actions = (FilterAction, )
        multi_select = False

    def get_object_id(self, datum):
        return datum.name
