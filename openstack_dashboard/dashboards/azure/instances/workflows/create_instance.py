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
import re

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api


LOG = logging.getLogger(__name__)

INSTANCE_NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-]*$", re.UNICODE)
INSTANCE_ERROR_MESSAGES = {
    'invalid': _('Instance name must begin with letter and only contain'
                 ' letters, numbers and hyphens.')}


class SelectProjectUserAction(workflows.Action):
    project_id = forms.ChoiceField(label=_("Project"))
    user_id = forms.ChoiceField(label=_("User"))
    subscription_id = forms.ChoiceField(label=_("Subscription"))

    def __init__(self, request, *args, **kwargs):
        super(SelectProjectUserAction, self).__init__(request, *args, **kwargs)
        # Set our project choices
        projects = [(tenant.id, tenant.name)
                    for tenant in request.user.authorized_tenants]
        self.fields['project_id'].choices = projects

        # Set our user options
        users = [(request.user.id, request.user.username)]
        self.fields['user_id'].choices = users

        # Set our subscription options
        subscriptions = [(tenant.subscription_id, tenant.subscription_name)
                         for tenant in request.user.authorized_tenants]
        self.fields['subscription_id'].choices = subscriptions

    class Meta:
        name = _("Project & User")
        # Unusable permission so this is always hidden. However, we
        # keep this step in the workflow for validation/verification purposes.
        permissions = ("!",)


class SelectProjectUser(workflows.Step):
    action_class = SelectProjectUserAction
    contributes = ("project_id", "user_id", "subscription_id")


class SetInstanceDetailsAction(workflows.Action):
    name = forms.RegexField(max_length=255,
                            label=_("Instance Name"),
                            regex=INSTANCE_NAME_REGEX,
                            error_messages=INSTANCE_ERROR_MESSAGES)

    role_size_type = forms.ChoiceField(
        label=_("VM Size Basic Spec"),
        help_text=_("Choose Your Boot Source Type."))

    flavor_basic = forms.ChoiceField(
        label=_("Flavor"),
        help_text=_("Size of image to launch."),
        required=False)

    flavor_standard = forms.ChoiceField(
        label=_("Flavor"),
        help_text=_("Size of image to launch."),
        required=False)

    # Disk/Volume Instance Creation is not allowed temporarily
    # disk_snapshot = forms.ChoiceField
    # disk_as_image = forms.ChoiceField

    class Meta:
        name = _("Details")
        help_text_template = ("azure/instances/"
                              "_launch_details_help.html")

    def __init__(self, request, context, *args, **kwargs):
        self.request = request
        self.context = context
        super(SetInstanceDetailsAction, self).__init__(
            request, context, *args, **kwargs)

        role_size_type_choices = [
            ("flavor_basic", _("Basic")),
            ("flavor_standard", _("Standard")),
        ]
        self.fields['role_size_type'].choices = role_size_type_choices

    @memoized.memoized_method
    def _get_role_size_list(self):
        try:
            flavors = api.azure_api.role_size_list(self.request)
        except Exception:
            flavors = []
            exceptions.handle(self.request,
                              _('Unable to retrieve azure role size list.'))
        return flavors

    def _check_flavor_basic(self, cleaned_data):
        if not cleaned_data.get('flavor_basic'):
            msg = _("You must select a basic flavor.")
            self._errors['flavor_basic'] = self.error_class([msg])

    def _check_flavor_standard(self, cleaned_data):
        if not cleaned_data.get('flavor_standard'):
            msg = _("You must select a standard flavor.")
            self._errors['flavor_standard'] = self.error_class([msg])

    def _check_flavor(self, cleaned_data):
        # Validate our instance source.
        role_size_type = self.data.get('role_size_type', None)
        flavor_check_methods = {
            'basic': self._check_flavor_basic,
            'standard': self._check_flavor_standard
        }
        check_method = flavor_check_methods.get(role_size_type)
        if check_method:
            check_method(cleaned_data)

    def clean(self):
        cleaned_data = super(SetInstanceDetailsAction, self).clean()

        self._check_flavor(cleaned_data)

        return cleaned_data

    def populate_flavor_basic_choices(self, request, context):
        rolesizes = self._get_role_size_list()
        rolesize_list = [(r.name, r.label)for r in sorted(
            rolesizes,
            key=lambda x: x.cores,
            reverse=False)if r.name[:6] == 'Basic_']

        return rolesize_list

    def populate_flavor_standard_choices(self, request, context):
        rolesizes = self._get_role_size_list()
        rolesize_list = [(r.name, r.label) for r in sorted(
            rolesizes,
            key=lambda x: x.cores,
            reverse=False) if r.name[:6] != 'Basic_']

        return rolesize_list


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    depends_on = ("project_id", "user_id", "subscription_id")
    contributes = ("name", "role_size_type", "rolesize_name")

    def contribute(self, data, context):
        context = super(SetInstanceDetails, self).contribute(data, context)

        # Translate form input to context for source values.
        if "role_size_type" in data:
            if data["role_size_type"] in ["flavor_basic", ]:
                context["rolesize_name"] = data.get("flavor_basic", None)
            else:
                context["rolesize_name"] = data.get("flavor_standard", None)

        return context


class SetAzureOSImageAction(workflows.Action):
    azure_source_type = forms.ChoiceField(
        label=_("Instance Boot Source"),
        help_text=_("Choose Your Boot Source Type."))

    windows_image_id = forms.ChoiceField(
        label=_("Windows Image"),
        help_text=_("Choose version of your windows"
                    " instance operating system."),
        required=False)

    linux_image_id = forms.ChoiceField(
        label=_("Linux Image"),
        help_text=_("Choose version of your linux"
                    " instance operating system."),
        required=False)

    def __init__(self, *args):
        super(SetAzureOSImageAction, self).__init__(*args)

        source_type_choices = [
            ("windows_image_id", _("Boot from windows image")),
            ("linux_image_id", _("Boot from linux image")),
            # ("disk_snapshot", _("Boot from your disk")),
            # ("disk_as_image", _("Boot from your image")),
        ]
        self.fields['azure_source_type'].choices = source_type_choices

    @memoized.memoized_method
    def _get_avaiable_os_images(self):
        try:
            images = api.azure_api.list_os_images(self.request)
        except Exception:
            images = []
            exceptions.handle(self.request,
                              _('Unable to retrieve azure os image list.'))
        return images

    def _check_source_windows_image_id(self, cleaned_data):
        if not cleaned_data.get('windows_image_id'):
            msg = _("You must select a windows image.")
            self._errors['windows_image_id'] = self.error_class([msg])

    def _check_source_linux_image_id(self, cleaned_data):
        if not cleaned_data.get('linux_image_id'):
            msg = _("You must select a linux image.")
            self._errors['linux_image_id'] = self.error_class([msg])

    def _check_source(self, cleaned_data):
        # Validate our instance source.
        azure_source_type = self.data.get('azure_source_type', None)
        source_check_methods = {
            'windows_image_id': self._check_source_windows_image_id,
            'linux_image_id': self._check_source_linux_image_id
        }
        check_method = source_check_methods.get(azure_source_type)
        if check_method:
            check_method(cleaned_data)

    def clean(self):
        cleaned_data = super(SetAzureOSImageAction, self).clean()
        self._check_source(cleaned_data)
        return cleaned_data

    def populate_windows_image_id_choices(self, request, context):
        images = self._get_avaiable_os_images()
        image_list = [(i.name, i.label)
                      for i in images if i.os == 'Windows']
        image_list.sort()

        return image_list

    def populate_linux_image_id_choices(self, request, context):
        images = self._get_avaiable_os_images()
        image_list = [(i.name, i.label)
                      for i in images if i.os == 'Linux']
        image_list.sort()

        return image_list

    class Meta:
        name = _("OS Image")
        help_text_template = ("azure/instances/"
                              "_launch_images_help.html")


class SetAzureOSImageStep(workflows.Step):
    action_class = SetAzureOSImageAction
    contributes = ("azure_source_type", "os_image_name")

    def contribute(self, data, context):
        context = super(SetAzureOSImageStep, self).contribute(data, context)

        if "azure_source_type" in data:
            if data["azure_source_type"] in ["windows_image_id", ]:
                context["os_image_name"] = data.get("windows_image_id", None)
            else:
                context["os_image_name"] = data.get("linux_image_id", None)

        return context


class SetAccessControlsAction(workflows.Action):
    access_user_name = forms.CharField(
        label=_("OS Username"),
        help_text=_("An OS user name which is"
                    " this instance's administrator."))

    admin_pass = forms.RegexField(
        label=_("Admin Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})

    confirm_admin_pass = forms.CharField(
        label=_("Confirm Admin Password"),
        widget=forms.PasswordInput(render_value=False))

    location = forms.ChoiceField(
        label=_("Location"),
        help_text=_("The data center to launch the instance."))

    enable_port = forms.BooleanField(
        label=_("Enable SSH/Remote Desktop/PowerShell"),
        required=False,
        help_text=_("Enable SSH/Remote Desktop/PowerShell port."))

    cloud_services = forms.ChoiceField(
        label=_("Cloud Services"),
        help_text=_("Choose/new a cloud service."))
    cloud_service_name = forms.CharField(
        label=_("New Cloud Service Name"),
        required=False)

    class Meta:
        name = _("Access & Security")
        help_text = _("Control access to your instance via key pairs, "
                      "passwords, and other mechanisms.")

    def __init__(self, request, *args, **kwargs):
        super(SetAccessControlsAction, self).__init__(request, *args, **kwargs)

    def populate_cloud_services_choices(self, request, context):
        try:
            cloud_services = api.azure_api.cloud_service_list(request)
        except Exception:
            cloud_services = []
            exceptions.handle(
                self.request,
                _('Unable to retrieve azure cloud service list.'))

        cs_list = [(cs.service_name, cs.service_name)
                   for cs in cloud_services]
        cs_list.sort()
        cs_list.insert(0, ("new_cloudservice", _("Add a new cloud service")))
        return cs_list

    def populate_location_choices(self, request, context):
        try:
            locations = api.azure_api.location_list(request)
        except Exception:
            locations = []
            exceptions.handle(request,
                              _('Unable to retrieve azure location list.'))

        location_list = [
            (l.name, l.display_name)
            for l in locations if 'Compute' in l.available_services]
        location_list.sort()
        if not location_list:
            location_list.insert(
                0, ("", _("No availability locations found")))

        return location_list

    def clean(self):
        '''Check to make sure password fields match.'''
        cleaned_data = super(SetAccessControlsAction, self).clean()
        if 'admin_pass' in cleaned_data:
            if cleaned_data['admin_pass'] != cleaned_data.get(
                    'confirm_admin_pass', None):
                raise forms.ValidationError(_('Passwords do not match.'))

        if 'cloud_services' in cleaned_data:
            if (cleaned_data['cloud_services'] == 'new_cloudservice'
                    and cleaned_data.get('cloud_service_name', '') == ''):
                msg = _("You must set a cloud service name.")
                self._errors['cloud_service_name'] = self.error_class([msg])

        if 'location' in cleaned_data:
            if cleaned_data['location'] == "":
                msg = _("No availability locations found")
                self._errors['location'] = self.error_class([msg])

        return cleaned_data


class SetAccessControls(workflows.Step):
    action_class = SetAccessControlsAction
    depends_on = ("project_id", "user_id", "subscription_id")
    contributes = ("access_user_name",
                   "admin_pass", "confirm_admin_pass",
                   "location",
                   "enable_port",
                   "cloud_services",
                   "cloud_service_name")

    def contribute(self, data, context):
        context = super(SetAccessControls, self).contribute(data, context)

        if "cloud_services" in data:
            if data["cloud_services"] != 'new_cloudservice':
                context["cloud_service_name"] = data.get("cloud_services",
                                                         None)

        if data:
            context['admin_pass'] = data.get("admin_pass", "")
            context['confirm_admin_pass'] = data.get("confirm_admin_pass", "")
        return context


class LaunchInstance(workflows.Workflow):
    slug = "launch_instance"
    name = _("Launch Instance")
    finalize_button_name = _("Launch")
    success_message = _('Launched instance named "%s".')
    failure_message = _('Unable to launch instance named "%s".')
    multipart = True
    default_steps = (SelectProjectUser,
                     SetInstanceDetails,
                     SetAzureOSImageStep,
                     SetAccessControls)

    def get_success_url(self):
        return reverse("horizon:azure:instances:index")

    def get_failure_url(self):
        return reverse("horizon:azure:instances:index")

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % name

    @sensitive_variables('context')
    def handle(self, request, context):
        try:
            vm_name = context.get('name', None)
            role_size = context.get('rolesize_name', None)
            os_image_name = context.get('os_image_name', None)
            access_user = context.get('access_user_name', None)
            service_name = context["cloud_service_name"]
            image_type = context['azure_source_type']
            user_password = context['admin_pass']
            location = context['location']
            enable_port = context['enable_port']

            create_new_cloudservice = True if (context['cloud_services'] ==
                                               'new_cloudservice') else False
            # do create
            api.azure_api.virtual_machine_create(
                request,
                service_name=service_name,
                location=location,
                create_new_cloudservice=create_new_cloudservice,
                deployment_name=service_name,
                label=vm_name,
                enable_port=enable_port,
                role_name=vm_name,
                image_name=os_image_name,
                image_type=image_type,
                admin_username=access_user,
                user_password=user_password,
                role_size=role_size)
            return True
        except Exception as e:
            exceptions.handle(request, str(e))
            return False
