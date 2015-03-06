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


def get_location(cloudservice):
    return getattr(cloudservice, 'hosted_service_properties').location


def get_date_created(cloudservice):
    return getattr(cloudservice,
                   'hosted_service_properties').date_created


def get_status(cloudservice):
    return getattr(cloudservice,
                   'hosted_service_properties').status


def get_date_last_modified(cloudservice):
    return getattr(cloudservice,
                   'hosted_service_properties').date_last_modified


class DeleteDeployment(tables.BatchAction):
    name = "deletedeployment"
    classes = ("btn-danger",)
    help_text = _("To perform this action you must "
                  "confirm the cloud service has deployment."
                  " Deleted deployment is not recoverable."
                  " All resources in the deployment will be deleted.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Deployment",
            u"Delete Deployments",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Deployment",
            u"Deleted Deployments",
            count
        )

    def allowed(self, request, datum=None):
        if datum:
            cs = api.azure_api.cloud_service_detail(request,
                                                    datum.service_name,
                                                    True)
            if cs.deployments is None or len(cs.deployments) == 0:
                return False
        return True

    def action(self, request, obj_id):
        cs = api.azure_api.cloud_service_detail(request, obj_id, True)
        if cs.deployments is not None:
            for dep in cs.deployments:
                api.azure_api.deployment_delete(request,
                                                cs.service_name,
                                                dep.name)


class DeleteCloudService(tables.DeleteAction):
    help_text = _("Deleted cloud service are not recoverable. "
                  "All resources in this cloud service will be deleted.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Cloud Service",
            u"Delete Cloud Services",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Cloud Service",
            u"Deleted Cloud Services",
            count
        )

    def allowed(self, request, datum=None):
        if datum:
            cs = api.azure_api.cloud_service_detail(request,
                                                    datum.service_name,
                                                    True)
            if cs.deployments and len(cs.deployments) > 0:
                return False
        return True

    def delete(self, request, obj_id):
        api.azure_api.cloud_service_delete(request, obj_id)


class CreateCloudService(tables.LinkAction):
    name = "createcloudservcie"
    verbose_name = _("Create Cloud Servcie")
    classes = ("btn-rebuild", "ajax-modal")
    url = "horizon:lecloud:cloudservices:create"


def get_detail_link(datum):
    url = "horizon:lecloud:cloudservices:detail"
    return urlresolvers.reverse(url, args=[datum.service_name])


class CloudServicesTable(tables.DataTable):
    service_name = tables.Column("service_name",
                                 link=get_detail_link,
                                 verbose_name=_("Name"))
    location = tables.Column(get_location,
                             verbose_name=_("Location"))
    status = tables.Column(get_status,
                           verbose_name=_("Status"))
    date_last_modified = tables.Column(get_date_last_modified,
                                       verbose_name=_("Date Last Modified"))
    date_created = tables.Column(get_date_created,
                                 verbose_name=_("Date Created"))

    class Meta(object):
        name = 'cloud_services'
        verbose_name = _('Cloud Services')
        table_actions = (FilterAction,
                         CreateCloudService,
                         DeleteCloudService)
        row_actions = (DeleteDeployment, DeleteCloudService)

    def get_object_display(self, datum):
        return datum.service_name

    def get_object_id(self, datum):
        return datum.service_name
