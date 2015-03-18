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

from django.conf import settings
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

# Leave this REGEX here for future use.
PASS_REGEX = re.compile(
    r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[a-zA-Z0-9.,/?@#$%_=+-|]{6,72}$",
    re.UNICODE)
PASS_ERROR_MESSAGES = {
    'invalid': _('The supplied password must be 6-72 characters.'
                 ' Password must contain uppercase and lowercase'
                 ' letters and numbers. And some special character'
                 ' like: .,/?@#$%_=+-|')}

INSTANCE_NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-]{2,14}$", re.UNICODE)
INSTANCE_NAME_HELP_TEXT = _('Instance name must begin with letter'
                            ' and only contain'
                            ' letters, numbers and hyphens.'
                            ' And length at 3-15.')
INSTANCE_ERROR_MESSAGES = {'invalid': INSTANCE_NAME_HELP_TEXT}

RESERVED_USERNAME = getattr(settings,
                            "RESERVED_USERNAME",
                            ('admin', 'administrator', 'root', 'a'))

NAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-]*$", re.UNICODE)
CLOUD_SERVICE_NAME_HELP_TEXT = _(
    'Cloud service name must begin with letter'
    ' and only contain letters, numbers and hyphens.'
    ' Cloud service name must be globally unique.')
CLOUD_SERVICE_ERROR_MESSAGES = {'invalid': CLOUD_SERVICE_NAME_HELP_TEXT}

# reserved for future use
FLAVOR_DISPLAY_CHOICE = {
    'A5': _('A5 (2 cores, 14336 MB)'),
    'A6': _('A6 (4 cores, 28672 MB)'),
    'A7': _('A7 (8 cores, 57344 MB)'),
    'Basic_A0': _('Basic_A0 (1 cores, 768 MB)'),
    'Basic_A1': _('Basic_A1 (1 cores, 1792 MB)'),
    'Basic_A2': _('Basic_A2 (2 cores, 3584 MB)'),
    'Basic_A3': _('Basic_A3 (4 cores, 7168 MB)'),
    'Basic_A4': _('Basic_A4 (8 cores, 14336 MB)'),
    'ExtraLarge': _('ExtraLarge (8 cores, 14336 MB)'),
    'ExtraSmall': _('ExtraSmall (1 cores, 768 MB)'),
    'Large': _('Large (4 cores, 7168 MB)'),
    'Medium': _('Medium (2 cores, 3584 MB)'),
    'Small': _('Small (1 cores, 1792 MB)'),
    'Standard_D1': _('Standard_D1 (1 cores, 3584 MB)'),
    'Standard_D11': _('Standard_D11 (2 cores, 14336 MB)'),
    'Standard_D12': _('Standard_D12 (4 cores, 28672 MB)'),
    'Standard_D13': _('Standard_D13 (8 cores, 57344 MB)'),
    'Standard_D14': _('Standard_D14 (16 cores, 114688 MB)'),
    'Standard_D2': _('Standard_D2 (2 cores, 7168 MB)'),
    'Standard_D3': _('Standard_D3 (4 cores), 14336 MB)'),
    'Standard_D4': _('Standard_D4 (8 cores), 28672 MB)')}

LOCATION_DISPLAY_CHOICE = getattr(
    settings,
    "LOCATION_DISPLAY_CHOICE",
    {"China East": _("China East"),
     "China North": _("China North")})


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

    class Meta(object):
        name = _("Project & User")
        # Unusable permission so this is always hidden. However, we
        # keep this step in the workflow for validation/verification purposes.
        permissions = ("!",)


class SelectProjectUser(workflows.Step):
    action_class = SelectProjectUserAction
    contributes = ("project_id", "user_id", "subscription_id")


class SetInstanceDetailsAction(workflows.Action):
    name = forms.RegexField(max_length=15,
                            label=_("Instance Name"),
                            regex=INSTANCE_NAME_REGEX,
                            error_messages=INSTANCE_ERROR_MESSAGES,
                            help_text=INSTANCE_NAME_HELP_TEXT)

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

    # Disk/Volume Instance Creation is not allowed temporarily
    # disk_snapshot = forms.ChoiceField
    # disk_as_image = forms.ChoiceField

    class Meta(object):
        name = _("Details")
        help_text_template = ("lecloud/instances/"
                              "_launch_details_help.html")

    def __init__(self, request, context, *args, **kwargs):
        self.request = request
        self.context = context
        super(SetInstanceDetailsAction, self).__init__(
            request, context, *args, **kwargs)

        project = next((proj for proj in request.user.authorized_tenants
                        if proj.id == request.user.project_id), None)

        role_size_type_choices = [
            ("flavor_basic", _("Basic")),
        ]

        if not getattr(project, "is_test", None):
            role_size_type_choices.append(("flavor_standard", _("Standard")))
        self.fields['role_size_type'].choices = role_size_type_choices

    @memoized.memoized_method
    def _get_role_size_list(self):
        try:
            flavors = api.azure_api.role_size_list(self.request)
        except Exception:
            flavors = []
            exceptions.handle(self.request,
                              _('Unable to retrieve role size list.'))
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

    def _check_quotas(self, cleaned_data):
        # Prevent launching more instances than the quota allows
        subscription = api.azure_api.subscription_get(self.request)
        flavor_basic = cleaned_data.get('flavor_basic')
        flavor_type = cleaned_data.get(flavor_basic)
        flavors = self._get_role_size_list()
        flavors_dict = dict([(r.name, r) for r in flavors])
        flavor = flavors_dict.get(flavor_type)

        count_error = []
        # Validate cores.
        available_cores = subscription.max_core_count - \
            subscription.current_core_count
        if flavor and available_cores < flavor.cores:
            count_error.append(_("Cores(Available: %(avail)s, "
                                 "Requested: %(req)s)")
                               % {'avail': available_cores,
                                  'req': flavor.cores})

        if count_error:
            value_str = ", ".join(count_error)
            msg = (_('The requested instance cannot be launched. '
                     'The following requested resource(s) exceed '
                     'quota(s): %s.') % value_str)
            self._errors['flavor_basic'] = self.error_class([msg])

    def clean(self):
        cleaned_data = super(SetInstanceDetailsAction, self).clean()

        self._check_flavor(cleaned_data)
        self._check_quotas(cleaned_data)

        return cleaned_data

    def populate_flavor_basic_choices(self, request, context):
        rolesizes = self._get_role_size_list()
        rolesize_list = [(r.name, r.label) for r in sorted(
            rolesizes,
            key=lambda x: x.cores,
            reverse=False)if r.name[:6] == 'Basic_']

        return rolesize_list

    def populate_flavor_standard_choices(self, request, context):
        rolesizes = self._get_role_size_list()
        a_types = [(r.name, r.label) for r in sorted(
            rolesizes,
            key=lambda x: x.memory_in_mb,
            reverse=False) if (r.name[:6] != 'Basic_'
                               and r.name[0:9] != 'Standard_')]
        d_types = [(r.name, r.label) for r in sorted(
            rolesizes,
            key=lambda x: x.memory_in_mb,
            reverse=False) if r.name[0:9] == 'Standard_']

        return a_types + d_types


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
        label=_("Operating System Type"),
        help_text=_("Choose an operating system type."))

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
        image_list = []
        for i in images:
            if i.os == 'Windows':
                if i.published_date is None or i.published_date == '':
                    display = i.label
                else:
                    display = "%(label)s - %(date)s" % {
                        "label": i.label, "date": i.published_date[0:10]}
                image_list.append((i.name, display))

        image_list.sort()

        return image_list

    def populate_linux_image_id_choices(self, request, context):
        images = self._get_avaiable_os_images()
        image_list = []
        for i in images:
            if i.os == 'Linux':
                if i.published_date is None or i.published_date == '':
                    display = i.label
                else:
                    display = "%(label)s - %(date)s" % {
                        "label": i.label, "date": i.published_date[0:10]}
                image_list.append((i.name, display))

        image_list.sort()

        return image_list

    class Meta(object):
        name = _("OS Image")
        help_text_template = ("lecloud/instances/"
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
    access_user_name = forms.RegexField(
        label=_("Username"),
        help_text=_("An operating system user name which is"
                    " this instance's administrator."),
        max_length=255,
        regex=NAME_REGEX,
        error_messages=CLOUD_SERVICE_ERROR_MESSAGES)

    admin_pass = forms.RegexField(
        label=_("Password"),
        max_length=72,
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()},
        help_text=validators.password_validator_msg())

    confirm_admin_pass = forms.CharField(
        label=_("Confirm Password"),
        max_length=72,
        widget=forms.PasswordInput(render_value=False))

    enable_port = forms.BooleanField(
        label=_("Enable SSH/Remote Desktop/PowerShell"),
        required=False,
        help_text=_("Linux will enable SSH port."
                    " Windows will enable Remote Desktop and PowerShell."))

    cloud_services = forms.ChoiceField(
        label=_("Cloud Services"),
        help_text=_("Choose or create a cloud service."))

    cloud_service_name = forms.RegexField(
        max_length=255,
        label=_("Cloud Service Name"),
        regex=NAME_REGEX,
        error_messages=CLOUD_SERVICE_ERROR_MESSAGES,
        help_text=CLOUD_SERVICE_NAME_HELP_TEXT,
        required=False)

    location = forms.ChoiceField(
        label=_("Location"),
        help_text=_("The data center to launch the instance(Cloud Service)."))

    class Meta(object):
        name = _("Access & Security")
        help_text_template = ("lecloud/instances/"
                              "_launch_security_help.html")

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

        cs_list = [(cs.service_name,
                    '%s - %s' % (cs.service_name,
                                 LOCATION_DISPLAY_CHOICE[
                                     cs.hosted_service_properties.location]))
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
                              _('Unable to retrieve location list.'))

        location_list = [
            (l.name, LOCATION_DISPLAY_CHOICE[l.name])
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
                    and cleaned_data.get('cloud_service_name', None) == ''):
                msg = _("You check the 'new cloud service',"
                        " so you need to set a cloud service name.")
                self._errors['cloud_service_name'] = self.error_class([msg])

        if 'location' in cleaned_data:
            if cleaned_data['location'] == "":
                msg = _("No availability locations found")
                self._errors['location'] = self.error_class([msg])

        if (cleaned_data.get('access_user_name')
                and cleaned_data.get('access_user_name').lower()
                in RESERVED_USERNAME):
            msg = _("You cannot use the reserved os username '%s'.") % \
                cleaned_data.get('access_user_name')
            self._errors['access_user_name'] = self.error_class([msg])

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
        return reverse("horizon:lecloud:instances:index")

    def get_failure_url(self):
        return reverse("horizon:lecloud:instances:index")

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % name

    @sensitive_variables('context')
    def handle(self, request, context):
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
        try:
            # do create
            return api.azure_api.virtual_machine_create(
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
        except Exception as e:
            exceptions.handle(request, str(e))
            return False
