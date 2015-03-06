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

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-]*$", re.UNICODE)

ENDPOINT_NAME_HELP_TEXT = _('Endpoint name must begin with letter'
                            ' and only contain'
                            ' letters, numbers and hyphens.')
ENDPOINT_ERROR_MESSAGES = {'invalid': ENDPOINT_NAME_HELP_TEXT}

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
    endpoint_name = forms.RegexField(
        max_length=255,
        label=_("Endpoint Name"),
        regex=NAME_REGEX,
        error_messages=ENDPOINT_ERROR_MESSAGES,
        help_text=ENDPOINT_NAME_HELP_TEXT)

    protocol = forms.ChoiceField(
        label=_("Protocol"),
        help_text=_("The protocol of the endpoint."))

    port = forms.IntegerField(
        label=_("Local Port"),
        help_text=_("The port of the instance. Available range(1-65535)"),
        max_value=65535,
        min_value=1)

    public_port = forms.IntegerField(
        label=_("Public Port"),
        help_text=_("The public port of the cloud service."
                    " You need to input an unused port."),
        max_value=65535,
        min_value=1)

    def __init__(self, request, *args, **kwargs):
        super(AddEndpointForm, self).__init__(request, *args, **kwargs)
        choices = [("tcp", _("TCP")),
                   ("udp", _("UDP"))]
        self.fields['protocol'].choices = choices

    def handle(self, request, data):
        cloud_service_name = data.get("cloud_service_name")
        deployment_name = data.get("deployment_name")
        instance_name = data.get("instance_name")

        endpoint_name = data.get("endpoint_name")
        protocol = data.get("protocol")
        local_port = data.get("port")
        public_port = data.get("public_port", None)
        try:
            api.azure_api.virtual_machine_add_endpoint(
                request,
                cloud_service_name, deployment_name,
                instance_name,
                endpoint_name, protocol,
                local_port, public_port)
            messages.success(
                request, _('Successfully add'
                           ' endpoint for instance "%s".') % instance_name)
        except Exception as e:
            redirect = reverse('horizon:lecloud:instances:index')
            msg = _("Unable to add endpoint to instance: %s") % e.message
            exceptions.handle(request, msg, redirect=redirect)
        return True


class RemoveEndpointForm(InstanceBaseOperationForm):
    endpoints = forms.ChoiceField(
        label=_("Endpoint"),
        help_text=_("Select an endpoint to remove. "
                    "Choice format 'endpoint name' - 'local port'"))

    def __init__(self, request, *args, **kwargs):
        super(RemoveEndpointForm, self).__init__(request, *args, **kwargs)

        endpoints = kwargs.get('initial', []).get('endpoints')
        choices = [(i.name, "%s - %s" % (i.name,
                                         i.local_port)) for i in endpoints]
        self.fields['endpoints'].choices = choices

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
            messages.success(
                request, _('Successfully remove'
                           ' endpoint from instance "%s".') % instance_name)
        except Exception:
            redirect = reverse('horizon:lecloud:instances:index')
            exceptions.handle(request,
                              _("Unable to remove instance endpoint."),
                              redirect=redirect)
        return True


class AttatchDatadiskForm(InstanceBaseOperationForm):
    disk_source = forms.ChoiceField(
        label=_('Disk Source'),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'source'}))

    size = forms.IntegerField(
        label=_("Data Disk Size(GB)"),
        max_value=1023,
        min_value=1,
        help_text=_("Size in 1 - 1023 GB."),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(AttatchDatadiskForm, self).__init__(request, *args, **kwargs)

        data_disks = kwargs.get('initial', []).get('data_disks')
        choices = [(i.name,
                    "%s - %s GB" % (
                        i.name,
                        i.logical_disk_size_in_gb)) for i in data_disks]
        choices.insert(0, ("new_disk", _("Add a new disk")))
        self.fields['disk_source'].choices = choices

    def clean(self):
        cleaned_data = super(AttatchDatadiskForm, self).clean()
        disk_source_type = self.cleaned_data.get('disk_source')
        if (disk_source_type == 'new_disk' and
                not cleaned_data.get('size')):
            msg = _("You check the 'Add a new disk',"
                    " so you need to set the disk size.")
            self._errors['size'] = self.error_class([msg])
        return cleaned_data

    def handle(self, request, data):
        cloud_service_name = data.get("cloud_service_name")
        deployment_name = data.get("deployment_name")
        instance_name = data.get("instance_name")

        disk_source = data.get("disk_source")
        size = data.get("size")
        try:
            if disk_source == "new_disk":
                api.azure_api.data_disk_attach(
                    request,
                    service_name=cloud_service_name,
                    deployment_name=deployment_name,
                    role_name=instance_name,
                    logical_disk_size_in_gb=size)
                messages.success(
                    request,
                    _('Successfully attach disk'
                      ' to instance %(instance_name)s.') %
                    {"instance_name": instance_name})
            else:
                api.azure_api.data_disk_attach(
                    request,
                    service_name=cloud_service_name,
                    deployment_name=deployment_name,
                    role_name=instance_name,
                    disk_name=disk_source)
                messages.success(
                    request,
                    _('Successfully attach disk %(disk_name)s'
                      ' for instance %(instance_name)s.') %
                    {"disk_name": disk_source,
                     "instance_name": instance_name})
        except Exception:
            redirect = reverse('horizon:lecloud:instances:index')
            exceptions.handle(request, _("Unable to attach disk"
                                         " for instance."),
                              redirect=redirect)
        return True


class DeattatchDatadiskForm(InstanceBaseOperationForm):
    data_disks = forms.ChoiceField(
        label=_("Data Disk"),
        help_text=_("Select an data disk to remove. "
                    "Choice format 'Disk name' - 'Size'"))

    def __init__(self, request, *args, **kwargs):
        super(DeattatchDatadiskForm, self).__init__(request, *args, **kwargs)

        data_disks = kwargs.get('initial', []).get('data_disks')
        choices = [(i.lun,
                    "%s - %s GB" % (
                        i.disk_name,
                        i.logical_disk_size_in_gb)) for i in data_disks]
        self.fields['data_disks'].choices = choices

    def handle(self, request, data):
        cloud_service_name = data.get("cloud_service_name")
        deployment_name = data.get("deployment_name")
        instance_name = data.get("instance_name")

        lun = data.get("data_disks")
        try:
            api.azure_api.data_disk_deattach(
                request,
                service_name=cloud_service_name,
                deployment_name=deployment_name,
                role_name=instance_name,
                lun=lun)
            messages.success(
                request,
                _('Successfully deattach data disk from instance.'))
        except Exception:
            redirect = reverse('horizon:lecloud:instances:index')
            exceptions.handle(request, _("Unable to deattach disk"
                                         " from instance."),
                              redirect=redirect)
        return True
