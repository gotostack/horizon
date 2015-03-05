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

NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-]*$", re.UNICODE)
NAME_HELP_TEXT = _('Cloud service name must begin with letter'
                   ' and only contain'
                   ' letters, numbers and hyphens.')
ERROR_MESSAGES = {'invalid': NAME_HELP_TEXT}


class CreateCloudServiceForm(forms.SelfHandlingForm):
    service_name = forms.RegexField(max_length=255,
                                    label=_("Cloud Service Name"),
                                    regex=NAME_REGEX,
                                    error_messages=ERROR_MESSAGES,
                                    help_text=NAME_HELP_TEXT)
    location = forms.ChoiceField(
        label=_("Location"),
        help_text=_("The data center to deploy the cloud service."))
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateCloudServiceForm, self).__init__(request, *args, **kwargs)
        locations = kwargs.get('initial', {}).get('locations')
        choices = [(l.name, l.display_name) for l in locations]
        self.fields['location'].choices = choices

    def handle(self, request, data):
        service_name = data.get("service_name")
        location = data.get("location")
        description = data.get("description", None)
        try:
            if api.azure_api.cloud_service_create(
                    request,
                    service_name=service_name,
                    label=service_name,
                    description=description,
                    location=location):
                messages.success(request,
                                 _('Successfully create'
                                   ' cloud service %s.') % service_name)
        except Exception as e:
            redirect = reverse('horizon:azure:cloudservices:index')
            exceptions.handle(request,
                              _("Unable to create cloud service: %s") % e,
                              redirect=redirect)
        return True
