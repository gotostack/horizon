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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api


class UpdateInstanceAvailabilitySetAction(workflows.Action):
    availability_set_name = forms.CharField(
        label=_("Availability Set Name"),
        required=False)

    class Meta(object):
        name = _("Availability Set")
        slug = 'availability_set'
        help_text = _("Edit the instance availability set.")


class UpdateInstanceAvailabilitySet(workflows.Step):
    action_class = UpdateInstanceAvailabilitySetAction
    depends_on = ("cloud_service_name", "deployment_name", "name",
                  "availability_set_name")
    contributes = ("availability_set_name",)


class UpdateInstance(workflows.Workflow):
    slug = "update_instance"
    name = _("Edit Instance")
    finalize_button_name = _("Save")
    success_message = _('Modified instance "%s".')
    failure_message = _('Unable to modify instance "%s".')
    success_url = "horizon:azure:instances:index"
    default_steps = (UpdateInstanceAvailabilitySet, )

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')

    def handle(self, request, context):
        cloud_service_name = context.get('cloud_service_name', None)
        deployment_name = context.get('deployment_name', None)
        instance_name = context.get('name', None)
        availability_set_name = context['availability_set_name']
        try:
            api.azure_api.virtual_machine_update(
                request,
                cloud_service_name,
                deployment_name,
                instance_name,
                availability_set_name=availability_set_name)
            return True
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
