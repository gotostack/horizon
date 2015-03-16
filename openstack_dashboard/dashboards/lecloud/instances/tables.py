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
from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode
from django.utils.translation import npgettext_lazy
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters

from openstack_dashboard import api
from openstack_dashboard.dashboards.lecloud.instances.workflows \
    import resize_instance
from openstack_dashboard.dashboards.lecloud.instances.workflows \
    import update_instance

LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("Started", "Starting", "Suspended")


def get_ips(instance):
    template_name = 'lecloud/instances/_instance_ips.html'
    context = {"instance": instance}
    return template.loader.render_to_string(template_name, context)


def get_endpoints(instance):
    template_name = 'lecloud/instances/_instance_endpoints.html'
    context = {"instance": instance}
    return template.loader.render_to_string(template_name, context)


def get_size(instance):
    if hasattr(instance, "role_size"):
        template_name = 'lecloud/instances/_instance_flavor.html'
        size_ram = sizeformat.mb_float_format(instance.role_size.memory_in_mb)
        temporary_disk = sizeformat.mb_float_format(
            instance.role_size.virtual_machine_resource_disk_size_in_mb)
        context = {
            "name": instance.role_size.name,
            "id": instance.role_name,
            "temporary_disk": temporary_disk,
            "size_ram": size_ram,
            "vcpus": instance.role_size.cores,
            "max_data_disk_count": instance.role_size.max_data_disk_count
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")


class DetailLink(tables.LinkAction):
    name = "detail"
    verbose_name = _("View Detail")
    url = "horizon:lecloud:instances:detail"

    def get_link_url(self, datum):
        return urlresolvers.reverse(self.url,
                                    args=(datum.cloud_service_name,
                                          datum.deployment_name,
                                          datum.instance_name))


def get_detail_link(datum):
    url = "horizon:lecloud:instances:detail"
    return urlresolvers.reverse(url,
                                args=(datum.cloud_service_name,
                                      datum.deployment_name,
                                      datum.instance_name))


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:lecloud:instances:launch"
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
                if q in i.role_name.lower()]


class TerminateInstance(tables.BatchAction):
    name = "terminate"
    classes = ("btn-danger",)
    icon = "off"
    help_text = _("The instance will be deleted, "
                  "memory and temporary disk data "
                  "will be deleted. The disks associated "
                  "with the instance are still in the disk repository.")

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
        try:
            datum = self.table.get_object_by_id(obj_id)
        except Exception:
            # TODO(Yulong) optimize, handle the exception
            # raise exceptions.HorizonException(
            #     _("The action cannot be performed at present. "
            #      "Please try again later."))
            messages.warning(
                request,
                _("The action cannot be performed at present. "
                  "Please try again later."))
            return False
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
            # it will raise a 409 (Conflict) error,
            # because the delete deployment request was not
            # completely finished.
            # User need to delete the cloud service in the cloud
            # services panel.
        else:
            api.azure_api.virtual_machine_delete(
                request,
                datum.cloud_service_name,
                # If instance was created from horizon,
                # the deployment name was same as cloud_service_name.
                datum.cloud_service_name,
                datum.instance_name)


class StartInstance(tables.BatchAction):
    name = "start"
    classes = ('btn-danger',)
    help_text = _("The instance will be started,"
                  " and begin to charge.")

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
        try:
            datum = self.table.get_object_by_id(obj_id)
        except Exception:
            messages.warning(
                request,
                _("The action cannot be performed at present. "
                  "Please try again later."))
            return False
        api.azure_api.virtual_machine_start(request,
                                            datum.cloud_service_name,
                                            datum.cloud_service_name,
                                            datum.instance_name)


class RestartInstance(tables.BatchAction):
    name = "restart"
    classes = ('btn-danger', 'btn-reboot')
    help_text = _("Restarted instances will lose"
                  " any data not saved in persistent storage.")

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
        try:
            datum = self.table.get_object_by_id(obj_id)
        except Exception:
            messages.warning(
                request,
                _("The action cannot be performed at present. "
                  "Please try again later."))
            return False
        api.azure_api.virtual_machine_restart(request,
                                              datum.cloud_service_name,
                                              datum.cloud_service_name,
                                              datum.instance_name)


class StopInstance(tables.BatchAction):
    name = "stop"
    classes = ('btn-danger',)
    help_text = _("Stopped instances will lose"
                  " any data not saved in persistent storage.")

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
        try:
            datum = self.table.get_object_by_id(obj_id)
        except Exception:
            messages.warning(
                request,
                _("The action cannot be performed at present. "
                  "Please try again later."))
            return False
        api.azure_api.virtual_machine_shutdown(request,
                                               datum.cloud_service_name,
                                               datum.cloud_service_name,
                                               datum.instance_name)


class ResizeLink(tables.LinkAction):
    name = "resize"
    verbose_name = _("Resize Instance")
    url = "horizon:lecloud:instances:resize"
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
    url = "horizon:lecloud:instances:update"
    classes = ("ajax-modal", "btn-danger")
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
    url = "horizon:lecloud:instances:addendpoint"

    def allowed(self, request, instance=None):
        return ((instance.power_state in ACTIVE_STATES)
                and instance.power_state.lower() != "deleting")

    def get_link_url(self, datum):
        return urlresolvers.reverse(
            self.url,
            args=[datum.cloud_service_name,
                  datum.deployment_name,
                  datum.instance_name])


class RemoveEndpoint(AddEndpoint):
    name = "removeendpoint"
    verbose_name = _("Remove Endpoint")
    url = "horizon:lecloud:instances:removeendpoint"


class AttachDataDisk(AddEndpoint):
    name = "attachdatadisk"
    verbose_name = _("Attach Data Disk")
    url = "horizon:lecloud:instances:attach"

    def allowed(self, request, instance=None):
        return ((instance.power_state in ACTIVE_STATES)
                and instance.power_state.lower() != "deleting"
                and (instance.role_size.max_data_disk_count -
                     len(instance.role.data_virtual_hard_disks) > 0))


class DeattachDataDisk(AddEndpoint):
    name = "de-attach"
    verbose_name = _("De-attach Data Disk")
    classes = ('btn-danger', "ajax-modal")
    url = "horizon:lecloud:instances:deattach"

    def allowed(self, request, instance=None):
        return ((instance.power_state == 'Started')
                and instance.power_state.lower() != "deleting"
                and len(instance.role.data_virtual_hard_disks) > 0)


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

    def get_data(self, request, obj_id):
        try:
            # To retrieve all vm size
            role_sizes = api.azure_api.role_size_list(request)
        except Exception:
            role_sizes = []
            exceptions.handle(request,
                              _('Unable to retrieve role size list.'))
        rolesize_dict = dict([(item.name, item) for item in role_sizes])

        cloudservice_name = obj_id[:obj_id.find("==")]
        instance_name = obj_id[obj_id.find("==") + 2:]

        instance = None
        if rolesize_dict:
            try:
                detail = api.azure_api.cloud_service_detail(
                    request,
                    cloudservice_name,
                    embed_detail=True)
                for dep in detail.deployments:
                    role_dict = dict([(r.role_name, r)
                                      for r in dep.role_list])
                    for ins in dep.role_instance_list:
                        ins.cloud_service_name = cloudservice_name
                        ins.deployment_name = dep.name
                        ins.role = role_dict.get(ins.role_name)
                        ins.role_size = rolesize_dict.get(
                            ins.role.role_size)
                        if instance_name == ins.role_name:
                            instance = ins
                            break
            except Exception:
                exceptions.handle(
                    request,
                    _('Unable to retrieve cloud service detail.'))
        return instance


class InstancesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Started", True),
        ("Suspended", True),
        ("Stopped", True),
    )
    NOT_READY_STATUS_CHOICES = (
        ("RunningTransitioning", False),
        ("SuspendedTransitioning", False),
        ("Starting", False),
        ("Suspending", False),
        ("Deploying", False),
        ("Deleting", False),
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
    power_state = tables.Column("power_state",
                                filters=(title, filters.replace_underscores),
                                status=True,
                                verbose_name=_("Power State"),
                                status_choices=STATUS_CHOICES,
                                display_choices=STATUS_DISPLAY_CHOICES)
    cloud_service_name = tables.Column("cloud_service_name",
                                       verbose_name=_("Cloud Service"))
    Endpoints = tables.Column(get_endpoints,
                              verbose_name=_("Endpoints"))

    def get_object_display(self, datum):
        return datum.role_name

    def get_object_id(self, datum):
        return '%s==%s' % (datum.cloud_service_name,
                           datum.role_name)

    class Meta(object):
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

    class Meta(object):
        name = 'instance_endpoints'
        verbose_name = _('Instance Endpoints')
        table_actions = (FilterAction, )
        multi_select = False

    def get_object_id(self, datum):
        return datum.name
