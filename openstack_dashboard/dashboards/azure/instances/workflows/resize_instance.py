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

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class SetFlavorChoiceAction(workflows.Action):
    old_flavor_id = forms.CharField(required=False, widget=forms.HiddenInput())
    old_flavor_name = forms.CharField(
        label=_("Old Flavor Type"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        required=False,
    )
    role_size_type = forms.ChoiceField(
        label=_("Size Spec"),
        help_text=_("Basic spec of virtual machine size."))

    flavor_basic = forms.ChoiceField(
        label=_("Flavor Basic"),
        help_text=_("Size of image to launch."),
        required=False)

    flavor_standard = forms.ChoiceField(
        label=_("Flavor Standard"),
        help_text=_("Size of image to launch."),
        required=False)

    class Meta(object):
        name = _("Flavor Choice")
        slug = 'flavor_choice'
        help_text_template = ("azure/instances/"
                              "_resize_instance_help.html")

    def __init__(self, request, context, *args, **kwargs):
        self.request = request
        self.context = context
        super(SetFlavorChoiceAction, self).__init__(
            request, context, *args, **kwargs)

        role_size_type_choices = [
            ("flavor_basic", _("Basic")),
            ("flavor_standard", _("Standard")),
        ]
        self.fields['role_size_type'].choices = role_size_type_choices

    def populate_flavor_basic_choices(self, request, context):
        old_flavor_id = context.get('old_flavor_id')
        flavors = context.get('flavors')

        rolesize_list = [(r.name, r.label) for r in sorted(
            flavors,
            key=lambda x: x.cores,
            reverse=False) if (r.name[:6] == 'Basic_' and
                               r.name != old_flavor_id)]

        return rolesize_list

    def populate_flavor_standard_choices(self, request, context):
        old_flavor_id = context.get('old_flavor_id')
        flavors = context.get('flavors')

        rolesize_list = [(r.name, r.label) for r in sorted(
            flavors,
            key=lambda x: x.cores,
            reverse=False) if (r.name[:6] != 'Basic_' and
                               r.name != old_flavor_id)]
        return rolesize_list


class SetFlavorChoice(workflows.Step):
    action_class = SetFlavorChoiceAction
    depends_on = ("cloud_service_name", "deployment_name", "name",
                  "old_flavor_id", "flavors")
    contributes = ("rolesize_name", "old_flavor_name")

    def contribute(self, data, context):
        context = super(SetFlavorChoice, self).contribute(data, context)

        # Translate form input to context for source values.
        if "role_size_type" in data:
            if data["role_size_type"] in ["flavor_basic", ]:
                context["rolesize_name"] = data.get("flavor_basic", None)
            else:
                context["rolesize_name"] = data.get("flavor_standard", None)

        return context


class ResizeInstance(workflows.Workflow):
    slug = "resize_instance"
    name = _("Resize Instance")
    finalize_button_name = _("Resize")
    success_message = _('Scheduled resize of instance "%s".')
    failure_message = _('Unable to resize instance "%s".')
    success_url = "horizon:azure:instances:index"
    default_steps = (SetFlavorChoice, )

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')

    @sensitive_variables('context')
    def handle(self, request, context):
        cloud_service_name = context.get('cloud_service_name', None)
        deployment_name = context.get('deployment_name', None)
        instance_name = context.get('name', None)
        rolesize_name = context.get('rolesize_name', None)
        try:
            api.azure_api.virtual_machine_resize(request,
                                                 cloud_service_name,
                                                 deployment_name,
                                                 instance_name,
                                                 rolesize_name)
            return True
        except Exception:
            exceptions.handle(request)
            return False
