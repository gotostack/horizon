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

import re

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

DISK_NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-]*$", re.UNICODE)
DISK_NAME_HELP_TEXT = _('Disk name must begin with letter'
                        ' and only contain'
                        ' letters, numbers and hyphens.')
DISK_ERROR_MESSAGES = {'invalid': DISK_NAME_HELP_TEXT}


class InstanceBaseOperationForm(forms.SelfHandlingForm):
    cloud_service_name = forms.CharField(widget=forms.HiddenInput())
    deployment_name = forms.CharField(widget=forms.HiddenInput())
    instance_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(InstanceBaseOperationForm,
              self).__init__(request, *args, **kwargs)
        cloud_service_name = kwargs.get('initial',
                                        {}).get('cloud_service_name')
        self.fields['cloud_service_name'].initial = cloud_service_name
        deployment_name = kwargs.get('initial', {}).get('deployment_name')
        self.fields['deployment_name'].initial = deployment_name
        instance_name = kwargs.get('initial', {}).get('instance_name')
        self.fields['instance_name'].initial = instance_name


class AddEndpointForm(InstanceBaseOperationForm):
    endpoint_name = forms.CharField(
        label=_("Endpoint Name"),
        help_text=_("The name of the endpoint."))
    protocol = forms.ChoiceField(
        label=_("Select Protocol"),
        help_text=_("The protocol of the endpoint."))
    port = forms.IntegerField(
        label=_("Local Port"),
        help_text=_("The port of the instance. Available range(1-65535)"),
        max_value=65535,
        min_value=1)

    def __init__(self, request, *args, **kwargs):
        super(AddEndpointForm, self).__init__(request, *args, **kwargs)
        choices = [("tcp", _("TCP")),
                   ("udp", _("UDP"))]
        self.fields['protocol'].choices = choices

    @sensitive_variables('data')
    def handle(self, request, data):
        cloud_service_name = data.get("cloud_service_name")
        deployment_name = data.get("deployment_name")
        instance_name = data.get("instance_name")

        endpoint_name = data.get("endpoint_name")
        protocol = data.get("protocol")
        port = data.get("port")
        try:
            api.azure_api.virtual_machine_add_endpoint(
                request,
                cloud_service_name, deployment_name,
                instance_name,
                endpoint_name, protocol, port)
            messages.success(request,
                             _('Successfully add'
                               ' endpoint for instance %s.') % instance_name)
        except Exception:
            redirect = reverse('horizon:azure:instances:index')
            exceptions.handle(request, _("Unable to add instance endpoint."),
                              redirect=redirect)
        return True


class RemoveEndpointForm(InstanceBaseOperationForm):
    endpoints = forms.ChoiceField(
        label=_("Endpoint"),
        help_text=_("Select an endpoint to remove."))

    def __init__(self, request, *args, **kwargs):
        super(RemoveEndpointForm, self).__init__(request, *args, **kwargs)

        endpoints = kwargs.get('initial', []).get('endpoints')
        choices = [(i.name, i.name) for i in endpoints]
        self.fields['endpoints'].choices = choices

    @sensitive_variables('data')
    def handle(self, request, data):
        cloud_service_name = data.get("cloud_service_name")
        deployment_name = data.get("deployment_name")
        instance_name = data.get("instance_name")

        endpoint_name = data.get("endpoints")
        try:
            api.azure_api.virtual_machine_remove_endpoint(
                request,
                cloud_service_name, deployment_name,
                instance_name,
                endpoint_name)
            messages.success(request,
                             _('Successfully remove'
                               ' endpoint for instance %s.') % instance_name)
        except Exception:
            redirect = reverse('horizon:azure:instances:index')
            exceptions.handle(request,
                              _("Unable to remove instance endpoint."),
                              redirect=redirect)
        return True


class AttatchDatadiskForm(InstanceBaseOperationForm):
    disk_name = forms.RegexField(max_length=255,
                                 label=_("Disk Name"),
                                 regex=DISK_NAME_REGEX,
                                 error_messages=DISK_ERROR_MESSAGES,
                                 help_text=DISK_NAME_HELP_TEXT)

    size = forms.IntegerField(
        label=_("Size"),
        max_value=1023,
        min_value=1,
        help_text=_("Size in 1 - 1023 GB."))

    def __init__(self, request, *args, **kwargs):
        super(AttatchDatadiskForm, self).__init__(request, *args, **kwargs)

    @sensitive_variables('data')
    def handle(self, request, data):
        cloud_service_name = data.get("cloud_service_name")
        deployment_name = data.get("deployment_name")
        instance_name = data.get("instance_name")

        disk_name = data.get("disk_name")
        size = data.get("size")
        try:
            api.azure_api.data_disk_attach(
                request,
                service_name=cloud_service_name,
                deployment_name=deployment_name,
                role_name=instance_name,
                logical_disk_size_in_gb=size)
            messages.success(
                request,
                _('Successfully attach disk %(disk_name)s'
                  ' for instance %(instance_name)s.') %
                {"disk_name": disk_name,
                 "instance_name": instance_name})
        except Exception:
            redirect = reverse('horizon:azure:instances:index')
            exceptions.handle(request, _("Unable to attach disk"
                                         " for instance."),
                              redirect=redirect)
        return True
