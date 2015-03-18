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

import datetime
import logging
import os
import random
import time

from azure.servicemanagement import ConfigurationSet  # noqa
from azure.servicemanagement import ConfigurationSetInputEndpoint  # noqa
from azure.servicemanagement import ConfigurationSetInputEndpoints
from azure.servicemanagement import LinuxConfigurationSet  # noqa
from azure.servicemanagement import LoadBalancerProbe  # noqa
from azure.servicemanagement import OSVirtualHardDisk  # noqa
from azure.servicemanagement import servicemanagementservice as sms
from azure.servicemanagement import WindowsConfigurationSet  # noqa
from azure import WindowsAzureConflictError
from azure import WindowsAzureError
from azure import WindowsAzureMissingResourceError

from azure.storage import blobservice

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.utils import azure_exceptions

LOG = logging.getLogger(__name__)

AZURE_MANAGEMENT_HOST = getattr(settings,
                                'AZURE_MANAGEMENT_HOST',
                                # Default China
                                'management.core.chinacloudapi.cn')

BLOB_SERVICE_HOST_BASE = '.blob.core.chinacloudapi.cn'
CN_STORAGE_BASE_URL = 'https://%s' + BLOB_SERVICE_HOST_BASE + '/%s/%s'
STORAGE_ACCOUNTS_SUFFIX = getattr(
    settings,
    "STORAGE_ACCOUNTS_SUFFIX",
    {"China East": "chinaeast", "China North": "chinanorth"})
VHDS_CONTAINER = getattr(settings, "VHDS_CONTAINER", "vhds")
SYS_DISK_BLOB_NAME_FORMAT = getattr(settings,
                                    "SYS_DISK_BLOB_NAME_FORMAT",
                                    "%s-%s-%s-sys-disk.vhd")

DATA_DISK_NAME_FORMAT = "%s-%s-data-disk-%s-%s"
DATA_DISK_BLOB_NAME_FORMAT = DATA_DISK_NAME_FORMAT + ".vhd"

STATUS_MAX_RETRY_TIMES = getattr(settings,
                                 "STATUS_MAX_RETRY_TIMES",
                                 60)
STATUS_RETRY_INTERVAL = getattr(settings,
                                "STATUS_RETRY_INTERVAL",
                                5)

AZURE_KEY_FILE_FOLDER = getattr(
    settings, 'AZURE_KEY_FILE_FOLDER',
    # getattr(settings, 'ROOT_PATH', ''),
    '/home/yulong/azure_keys/test/test_1')

RESERVED_ENDPOINT_NAME = {
    "REMOTE DESKTOP": "Remote Desktop",
    "REMOTEDESKTOP": "Remote Desktop",
    "POWER SHELL": "PowerShell",
    "POWERSHELL": "PowerShell",
    "SSH": "SSH",
    "FTP": "FTP",
    "SMTP": "SMTP",
    "DNS": "DNS",
    "HTTP": "HTTP",
    "POP3": "POP3",
    "IMAP": "IMAP",
    "LDAP": "LDAP",
    "HTTPS": "HTTPS",
    "SMTPS": "SMTPS",
    "IMAPS": "IMAPS",
    "POP3S": "POP3S",
    "MSSQL": "MSSQL",
    "MYSQL": "MYSQL"}


def _get_time_stamp():
    time = datetime.datetime.now()
    tm = '%d%d%d%d%d%d%d' % (
        time.year, time.month, time.day,
        time.hour, time.minute, time.second,
        time.microsecond)
    return tm


def create_new_key_for_subscription(project_id):
    """Create a new rsa key file for a tenant/subscription."""
    KEY_PEM = "%s/%s.pem" % (AZURE_KEY_FILE_FOLDER, project_id)
    KEY_CER = "%s/%s.cer" % (AZURE_KEY_FILE_FOLDER, project_id)
    os.system('openssl req -x509 -nodes'
              ' -days 365 -newkey rsa:1024'
              ' -keyout %s -out %s'
              ' -subj "/CN=%s"' % (KEY_PEM, KEY_PEM, project_id))
    os.system('openssl x509 -inform pem'
              ' -in %s -outform der -out %s' % (KEY_PEM, KEY_CER))


def get_tenant_pem_file_path(project_id):
    """Get the tenant pem file absolute path."""
    pem_path = "%s/%s.pem" % (AZURE_KEY_FILE_FOLDER, project_id)
    if os.path.exists(pem_path):
        return pem_path
    else:
        raise Exception("Subscription pem file does not exist.")


def get_tenant_cer_file_path(project_id):
    """Get the tenant cert file absolute path."""
    return "%s/%s.cer" % (AZURE_KEY_FILE_FOLDER, project_id)


def create_default_storage_accounts(project):
    subscription_id = project.subscription_id
    cert_file = get_tenant_pem_file_path(project.id)
    client = sms.ServiceManagementService(subscription_id,
                                          cert_file,
                                          host=AZURE_MANAGEMENT_HOST)
    for item in STORAGE_ACCOUNTS_SUFFIX.items():
        service_name = description = label = project.name + item[1]
        client.create_storage_account(service_name,
                                      description,
                                      label,
                                      location=item[0],
                                      geo_replication_enabled=False,
                                      account_type='Standard_LRS')
        storage_account = client.get_storage_account_keys(service_name)
        container_create(service_name,
                         storage_account.storage_service_keys.primary,
                         'vhds')


@memoized
def azureclient(request):
    """Get a new the Azure service management client.

    Need the authenticated/login user's subscription of tenant.
    """
    project = next((proj for proj in request.user.authorized_tenants
                    if proj.id == request.user.project_id), None)
    if project:
        subscription_id = project.subscription_id
        cert_file = get_tenant_pem_file_path(project.id)
        return sms.ServiceManagementService(subscription_id,
                                            cert_file,
                                            host=AZURE_MANAGEMENT_HOST,
                                            request_session=None)


@memoized
def subscription_get(request):
    """Azure location geographic domain."""
    return azureclient(request).get_subscription()


def subscription_quota_check(request, resource):
    sub = subscription_get(request)
    if resource == 'cores':
        return sub.max_core_count - sub.current_core_count > 0
    if resource == 'cloudservice':
        return sub.max_hosted_services - sub.current_hosted_services > 0


@memoized
def location_list(request):
    """Azure location geographic domain."""
    return azureclient(request).list_locations()


@memoized
def cloud_service_list(request):
    """Get all Azure Cloud Services of the subscription."""
    return azureclient(request).list_hosted_services()


@memoized
def cloud_service_detail(request, service_name, embed_detail=False):
    """Get details of one specific cloud service."""
    try:
        return azureclient(request).get_hosted_service_properties(
            service_name=service_name,
            embed_detail=embed_detail)
    except WindowsAzureMissingResourceError:
        raise azure_exceptions.AzureException(404, _("Not Found"))


def cloud_service_delete(request, service_name):
    """Delete a cloud service."""
    return azureclient(request).delete_hosted_service(service_name)


def cloud_service_create(request,
                         service_name, label, description=None,
                         location=None, affinity_group=None,
                         extended_properties=None):
    """Create a cloud service."""
    try:
        azureclient(request).create_hosted_service(
            service_name, label, description,
            location, affinity_group,
            extended_properties)
        return True
    except WindowsAzureConflictError:
        msg = _('A cloud service with name'
                ' "%s" is already existed.') % service_name
        messages.error(request, msg)
    return False


@memoized
def storage_account_list(request):
    """Get all Azure storage accounts of the subscription."""
    return azureclient(request).list_storage_accounts()


def storage_account_create(request, service_name, description, label,
                           affinity_group=None, location=None,
                           geo_replication_enabled=None,
                           extended_properties=None,
                           account_type='Standard_GRS'):
    """Creates a new storage account in Windows Azure."""
    return azureclient(request).create_storage_account(
        service_name,
        description, label,
        affinity_group, location,
        geo_replication_enabled,
        extended_properties,
        account_type)


@memoized
def affinity_group_list(request):
    """Get all Azure affinity group of the subscription."""
    return azureclient(request).list_affinity_groups()


@memoized
def role_size_list(request):
    """Get the list of available VM sizes (role sizes)."""
    return azureclient(request).list_role_sizes()


@memoized
def deployment_get_by_name(request, service_name, deployment_name):
    """Get deployment by name."""
    return azureclient(request).get_deployment_by_name(service_name,
                                                       deployment_name)


def deployment_create(request,
                      service_name, deployment_slot, name,
                      package_url, label, configuration,
                      start_deployment=False,
                      treat_warnings_as_error=False,
                      extended_properties=None):
    """Create a new deployment on staging or production."""
    return azureclient(request).create_deployment(
        service_name=service_name, deployment_slot=deployment_slot,
        name=name, package_url=package_url, label=label,
        configuration=configuration,
        start_deployment=start_deployment,
        treat_warnings_as_error=treat_warnings_as_error,
        extended_properties=extended_properties)


def deployment_delete(request, service_name, deployment_name):
    """Delete a azure deployment."""
    client = azureclient(request)
    result = client.delete_deployment(service_name,
                                      deployment_name)
    return _get_operation_status(client, result.request_id)


@memoized
def operating_systems_list(request):
    """Lists the versions of the guest operating system."""
    return azureclient(request).list_operating_systems()


@memoized
def list_os_images(request):
    """Get the list of available images."""
    return azureclient(request).list_os_images()


@memoized
def operating_system_families_list(request):
    """Get the list of available images family."""
    return azureclient(request).list_operating_system_families()


def _create_linux_ssh_endpoint():
    """Add ssh endpoint to a new linux vm network config."""
    network_config = ConfigurationSet()
    endpoint = ConfigurationSetInputEndpoint(name='SSH',
                                             protocol='tcp',
                                             port='10022',
                                             local_port='22')
    network_config.input_endpoints.input_endpoints.append(endpoint)
    return network_config


def _create_windows_endpoint():
    """Add Remote Desktop and PowerShell endpoints.

    to a new windows vm network config.
    """
    network_config = ConfigurationSet()
    endpoint = ConfigurationSetInputEndpoint(name='Remote Desktop',
                                             protocol='tcp',
                                             port='13389',
                                             local_port='3389')
    network_config.input_endpoints.input_endpoints.append(endpoint)

    endpoint2 = ConfigurationSetInputEndpoint(name='PowerShell',
                                              protocol='tcp',
                                              port='15986',
                                              local_port='5986')
    network_config.input_endpoints.input_endpoints.append(endpoint2)
    return network_config


def _get_cloudservice_used_public_ports(cloudservice):
    """Get all used public ports of one cloud service."""
    public_ports = []
    for dep in cloudservice.deployments:
        for role in dep.role_list:
            for conf in role.configuration_sets:
                if conf.input_endpoints:
                    for endpoint in conf.input_endpoints:
                        public_ports.append(endpoint.port)
    public_ports.sort()
    return public_ports


def get_role_instance_status(deployment, role_instance_name):
    """Get an instance status."""
    for role_instance in deployment.role_instance_list:
        if role_instance.instance_name == role_instance_name:
            return role_instance.instance_status
    return None


def virtual_machine_get(request, service_name,
                        deployment_name, role_name):
    """Get the detail of an instance."""
    try:
        return azureclient(request).get_role(service_name,
                                             deployment_name,
                                             role_name)
    except WindowsAzureMissingResourceError:
        raise azure_exceptions.AzureException(404, _("Not Found"))


def _get_virtual_machine_vhd_file_link(request, location,
                                       deployment_name,
                                       role_name):
    """Get the request related vm vhd file storage url."""
    project = next((proj for proj in request.user.authorized_tenants
                    if proj.id == request.user.project_id), None)
    if project:
        storage_account = project.name + STORAGE_ACCOUNTS_SUFFIX[location]
        vhd_file_blob = SYS_DISK_BLOB_NAME_FORMAT % (deployment_name,
                                                     role_name,
                                                     _get_time_stamp())
        return CN_STORAGE_BASE_URL % (storage_account,
                                      VHDS_CONTAINER,
                                      vhd_file_blob)
    else:
        return ''


def virtual_machine_create(request,
                           service_name,
                           create_new_cloudservice,
                           location,
                           deployment_name,
                           label, enable_port,
                           role_name,
                           image_name, image_type,
                           admin_username,
                           user_password,
                           deployment_slot='Production',
                           network_config=None,
                           availability_set_name=None,
                           data_virtual_hard_disks=None,
                           role_size=None,
                           role_type='PersistentVMRole',
                           virtual_network_name=None,
                           resource_extension_references=None,
                           provision_guest_agent=None,
                           vm_image_name=None,
                           media_location=None,
                           dns_servers=None,
                           reserved_ip_name=None):
    """Method for creating an azure virtual machine."""

    client = azureclient(request)

    if image_type == 'windows_image_id':
        conf = WindowsConfigurationSet(
            computer_name=role_name,
            admin_password=user_password,
            admin_username=admin_username)
        conf.domain_join = None
        conf.stored_certificate_settings = None
        conf.win_rm = None
        conf.additional_unattend_content = None
        if enable_port:
            network_config = _create_windows_endpoint()

    if image_type == 'linux_image_id':
        conf = LinuxConfigurationSet(
            host_name=role_name,
            user_name=admin_username,
            user_password=user_password,
            disable_ssh_password_authentication=False)
        if enable_port:
            network_config = _create_linux_ssh_endpoint()

    if create_new_cloudservice:
        # Create a new cloud service and a deployment for this new vm
        try:
            client.create_hosted_service(
                service_name=service_name,
                label=service_name,
                location=location)
            # TODO(Yulong) remove to azure_api.cloud_service_create
            # msg = _('Cloud service'
            #         ' "%s" was successfully created.') % service_name
            # messages.success(request, msg)
        except WindowsAzureConflictError:
            msg = _('A cloud service with name'
                    ' "%s" is already existed.') % service_name
            messages.error(request, msg)
            return False
        new_os_sys_disk_url = _get_virtual_machine_vhd_file_link(
            request,
            location,
            deployment_name,
            role_name)
        osvhd = OSVirtualHardDisk(
            source_image_name=image_name,
            media_link=new_os_sys_disk_url,
            # caching mode of the operating system disk
            # all default 'ReadOnly'
            host_caching='ReadOnly')
        result = client.create_virtual_machine_deployment(
            service_name=service_name,
            deployment_name=deployment_name,
            deployment_slot=deployment_slot,
            label=label,
            role_name=role_name,
            system_config=conf,
            os_virtual_hard_disk=osvhd,
            network_config=network_config,
            role_size=role_size)
        return _get_operation_status(client, result.request_id)
    else:
        cs = client.get_hosted_service_properties(
            service_name=service_name,
            embed_detail=True)
        new_os_sys_disk_url = _get_virtual_machine_vhd_file_link(
            request,
            cs.hosted_service_properties.location,
            deployment_name,
            role_name)
        osvhd = OSVirtualHardDisk(
            source_image_name=image_name,
            media_link=new_os_sys_disk_url,
            # caching mode of the operating system disk
            # all default 'ReadOnly'
            host_caching='ReadOnly')
        if cs.deployments:
            for dep in cs.deployments:
                for it in dep.role_list:
                    if role_name == it.role_name:
                        msg = _('An instance with name'
                                ' "%(role_name)s" in the cloud service'
                                ' "%(service_name)s" is already existed.') % {
                                    "role_name": role_name,
                                    "service_name": service_name}
                        messages.error(request, msg)
                        return False
            # Add this new vm to the existing cloud-service/deployment
            if enable_port:
                public_ports = _get_cloudservice_used_public_ports(cs)
                if public_ports:
                    # Random new public ports in the existing cloud service
                    for ep in network_config.input_endpoints.input_endpoints:
                        new_port = random.randint(int(public_ports[-1]),
                                                  int(public_ports[-1]) + 10)
                        ep.port = str(new_port)
                        public_ports.append(str(new_port))
            result = client.add_role(
                service_name=service_name,
                deployment_name=deployment_name,
                role_name=role_name,
                system_config=conf,
                os_virtual_hard_disk=osvhd,
                network_config=network_config,
                role_size=role_size)
            return _get_operation_status(client, result.request_id)
        else:
            # Cloud Service is existing but no deployment
            result = client.create_virtual_machine_deployment(
                service_name=service_name,
                deployment_name=deployment_name,
                deployment_slot=deployment_slot,
                label=label,
                role_name=role_name,
                system_config=conf,
                os_virtual_hard_disk=osvhd,
                network_config=network_config,
                role_size=role_size)
            return _get_operation_status(client, result.request_id)


def _get_operation_status(client, requestId):
    starttime = datetime.datetime.now()
    count = 0
    done = False
    while not done:
        operation = client.get_operation_status(requestId)
        count += 1

        if operation and operation.status == 'InProgress':
            time.sleep(STATUS_RETRY_INTERVAL)
        elif operation and operation.status == 'Succeeded':
            LOG.info("Request Id: %s Succeeded." % requestId)
            return True
        elif operation and operation.status == 'Failed':
            LOG.info("Request Id: %s Failed." % requestId)
            return False
        else:
            LOG.error("Unable to get request Id %s status." % requestId)

        if not done and count > STATUS_MAX_RETRY_TIMES:
            LOG.error("Request Id: %s time out." % requestId)
            return False

    endtime = datetime.datetime.now()
    LOG.info("Asynchronous request '%s' "
             "running time %s(s)." % (requestId,
                                      (endtime - starttime).seconds))
    return done


def virtual_machine_delete(request, service_name,
                           deployment_name, role_name):
    """Delete an azure virtual of a cloudservice/deployment."""
    client = azureclient(request)
    try:
        result = client.delete_role(
            service_name=service_name,
            deployment_name=deployment_name,
            role_name=role_name)
        return _get_operation_status(client, result.request_id)
    except (Exception,
            WindowsAzureError,
            WindowsAzureConflictError):
        raise azure_exceptions.AzureException(
            409, "An error occurred. Please try again later.")


def virtual_machine_shutdown(request, service_name,
                             deployment_name, role_name,
                             post_shutdown_action='StoppedDeallocated'):
    """Shutdown an azure vm of a cloudservice/deployment."""
    client = azureclient(request)
    try:
        result = client.shutdown_role(
            service_name=service_name,
            deployment_name=deployment_name,
            role_name=role_name,
            post_shutdown_action=post_shutdown_action)
        return _get_operation_status(client, result.request_id)
    except (Exception,
            WindowsAzureConflictError):
        raise azure_exceptions.AzureException(
            409, "An error occurred. Please try again later.")


def virtual_machine_restart(request, service_name, deployment_name, role_name):
    """Start an azure vm of a cloudservice/deployment."""
    client = azureclient(request)
    try:
        result = client.restart_role(service_name,
                                     deployment_name,
                                     role_name)
        return _get_operation_status(client, result.request_id)
    except (Exception,
            WindowsAzureConflictError):
        raise azure_exceptions.AzureException(
            409, "An error occurred. Please try again later.")


def virtual_machine_start(request, service_name, deployment_name, role_name):
    """Start an azure vm of a cloudservice/deployment."""
    client = azureclient(request)
    try:
        result = client.start_role(service_name,
                                   deployment_name,
                                   role_name)
        return _get_operation_status(client, result.request_id)
    except (Exception,
            WindowsAzureConflictError):
        raise azure_exceptions.AzureException(
            409, "An error occurred. Please try again later.")


def virtual_machine_capture(request, service_name, deployment_name,
                            role_name, post_capture_action,
                            target_image_name, target_image_label,
                            provisioning_configuration=None):
    """captures a virtual machine image to your image gallery."""
    client = azureclient(request)
    result = client.azureclient(request).capture_role(
        service_name, deployment_name, role_name,
        post_capture_action, target_image_name, target_image_label,
        provisioning_configuration)
    return _get_operation_status(client, result.request_id)


def virtual_machine_resize(request, service_name,
                           deployment_name, role_name,
                           role_size):
    """Resize an azure virtual machine."""
    client = azureclient(request)

    cs = client.get_hosted_service_properties(
        service_name=service_name,
        embed_detail=True)
    vm = client.get_role(service_name, deployment_name, role_name)

    if cs and vm:
        old_network_config = None
        for cf in vm.configuration_sets:
            old_network_config = cf if (cf.configuration_set_type ==
                                        'NetworkConfiguration') else None
        if old_network_config.input_endpoints is not None:
            for end in old_network_config.input_endpoints.input_endpoints:
                if end.load_balancer_probe is None:
                    end.load_balancer_probe = LoadBalancerProbe()

            if (old_network_config.subnet_names is None and
                    old_network_config.public_ips is None):
                new_conf = ConfigurationSet()
                new_conf.input_endpoints.input_endpoints = \
                    old_network_config.input_endpoints.input_endpoints
                old_network_config = new_conf
        else:
            old_network_config.input_endpoints = \
                ConfigurationSetInputEndpoints()
            old_network_config.input_endpoints.input_endpoints = []
            old_network_config.subnet_names = []

        result = client.update_role(
            service_name, deployment_name,
            role_name,
            network_config=old_network_config,
            role_size=role_size)
        return _get_operation_status(client, result.request_id)


def _get_instance_used_local_ports(instance, protocol):
    """Get all used endpoint names of an instance."""
    local_ports = []
    for cs in instance.configuration_sets:
        if cs.input_endpoints:
            for en in cs.input_endpoints:
                if str(protocol).lower() == str(en.protocol).lower():
                    local_ports.append(str(en.local_port).lower())
    local_ports.sort()
    return local_ports


def _get_instance_used_endpoint_name(instance):
    """Get all used endpoint names of an instance."""
    endpoint_names = []
    for cs in instance.configuration_sets:
        if cs.input_endpoints:
            for en in cs.input_endpoints:
                endpoint_names.append(en.name.lower())
    endpoint_names.sort()
    return endpoint_names


def virtual_machine_add_endpoint(request, service_name,
                                 deployment_name, role_name,
                                 endpoint_name, protocol,
                                 local_port,
                                 public_port=None,
                                 idle_timeout_in_minutes=4):
    """Add endpoint to an azure virtual machine."""
    client = azureclient(request)

    cs = client.get_hosted_service_properties(
        service_name=service_name,
        embed_detail=True)
    vm = client.get_role(service_name, deployment_name, role_name)

    endpoint_names = _get_instance_used_endpoint_name(vm)
    if endpoint_name.lower() in endpoint_names:
        raise azure_exceptions.AzureException(409,
                                              _("Endpoint name is in use."))

    local_ports = _get_instance_used_local_ports(vm, protocol)
    if str(local_port).lower() in local_ports:
        raise azure_exceptions.AzureException(409,
                                              _("Local port is in use."))

    public_ports = _get_cloudservice_used_public_ports(cs)
    if public_port and str(public_port) not in public_ports:
        new_port = str(public_port)
    elif public_port and str(public_port) in public_ports:
        raise azure_exceptions.AzureException(409,
                                              _("Public port is in use."))
    else:
        # Random a new public port in the existing cloud service
        new_port = random.randint(int(public_ports[-1]),
                                  int(public_ports[-1]) + 10)

    if cs and vm:
        if RESERVED_ENDPOINT_NAME.get(endpoint_name.upper()):
            endpoint_name = RESERVED_ENDPOINT_NAME[endpoint_name.upper()]
        network_config = None
        for cf in vm.configuration_sets:
            network_config = cf if (cf.configuration_set_type ==
                                    'NetworkConfiguration') else None
        if network_config and network_config.input_endpoints is not None:
            for end in network_config.input_endpoints.input_endpoints:
                if end.load_balancer_probe is None:
                    end.load_balancer_probe = LoadBalancerProbe()
            endpoint = ConfigurationSetInputEndpoint(
                name=endpoint_name,
                protocol=protocol,
                port=str(new_port),
                local_port=local_port,
                idle_timeout_in_minutes=idle_timeout_in_minutes)

            network_config.input_endpoints.input_endpoints.append(endpoint)
            if (network_config.subnet_names is None and
                    network_config.public_ips is None):
                new_conf = ConfigurationSet()
                new_conf.input_endpoints.input_endpoints = \
                    network_config.input_endpoints.input_endpoints
                network_config = new_conf
        else:
            network_config = ConfigurationSet()
            endpoint = ConfigurationSetInputEndpoint(
                name=endpoint_name,
                protocol=protocol,
                port=str(random.randint(10000, 10010)),
                local_port=local_port,
                idle_timeout_in_minutes=idle_timeout_in_minutes)
            network_config.input_endpoints.input_endpoints.append(endpoint)

    result = client.update_role(
        service_name, deployment_name,
        role_name,
        network_config=network_config)
    return _get_operation_status(client, result.request_id)


def virtual_machine_remove_endpoint(request, service_name,
                                    deployment_name, role_name,
                                    endpoint_name):
    """Remove endpoint from an azure virtual machine."""
    client = azureclient(request)

    cs = client.get_hosted_service_properties(
        service_name=service_name,
        embed_detail=True)
    vm = client.get_role(service_name, deployment_name, role_name)

    if cs and vm:
        network_config = None
        for cf in vm.configuration_sets:
            network_config = cf if (cf.configuration_set_type ==
                                    'NetworkConfiguration') else None

        if network_config and network_config.input_endpoints is not None:
            value = None
            for end in network_config.input_endpoints.input_endpoints:
                if end.load_balancer_probe is None:
                    end.load_balancer_probe = LoadBalancerProbe()
                if end.name.lower() == endpoint_name.lower():
                    value = end

            network_config.input_endpoints.input_endpoints.remove(value)
            if (network_config.subnet_names is None and
                    network_config.public_ips is None):
                new_conf = ConfigurationSet()
                new_conf.input_endpoints.input_endpoints = \
                    network_config.input_endpoints.input_endpoints
                network_config = new_conf
            result = client.update_role(
                service_name, deployment_name,
                role_name,
                network_config=network_config)
            return _get_operation_status(client, result.request_id)


def virtual_machine_update(request, service_name, deployment_name, role_name,
                           os_virtual_hard_disk=None, network_config=None,
                           availability_set_name=None,
                           data_virtual_hard_disks=None,
                           role_size=None, role_type='PersistentVMRole',
                           resource_extension_references=None,
                           provision_guest_agent=None):
    """Update an azure virtual machine."""
    client = azureclient(request)

    cs = client.get_hosted_service_properties(
        service_name=service_name,
        embed_detail=True)
    vm = client.get_role(service_name, deployment_name, role_name)

    if cs and vm:
        old_network_config = None
        for cf in vm.configuration_sets:
            old_network_config = cf if (cf.configuration_set_type ==
                                        'NetworkConfiguration') else None
        if old_network_config.input_endpoints is not None:
            for end in old_network_config.input_endpoints.input_endpoints:
                if end.load_balancer_probe is None:
                    end.load_balancer_probe = LoadBalancerProbe()

            if (old_network_config.subnet_names is None and
                    old_network_config.public_ips is None):
                new_conf = ConfigurationSet()
                new_conf.input_endpoints.input_endpoints = \
                    old_network_config.input_endpoints.input_endpoints
                old_network_config = new_conf
        else:
            old_network_config.input_endpoints = \
                ConfigurationSetInputEndpoints()
            old_network_config.input_endpoints.input_endpoints = []
            old_network_config.subnet_names = []

        result = client.update_role(
            service_name, deployment_name, role_name,
            os_virtual_hard_disk, old_network_config,
            availability_set_name, data_virtual_hard_disks,
            role_size, role_type,
            resource_extension_references,
            provision_guest_agent)
        return _get_operation_status(client, result.request_id)


def disk_list(request):
    """List all this subscription disks."""
    return azureclient(request).list_disks()


def disk_get(request, disk_name):
    '''Retrieves a disk from your image repository.'''
    try:
        return azureclient(request).get_disk(disk_name)
    except WindowsAzureMissingResourceError:
        raise azure_exceptions.AzureException(404, _("Not Found"))


def disk_delete(request, disk_name, delete_vhd=False):
    '''Deletes the specified data or operating system disk

    from your image repository.
    '''
    return azureclient(request).delete_disk(disk_name, delete_vhd)


def disk_add(request, has_operating_system,
             label, media_link, name, os):
    '''Adds a disk to the user image repository.'''
    return azureclient(request).add_disk(has_operating_system, label,
                                         media_link, name, os)


def disk_update(request, disk_name,
                has_operating_system,
                label, media_link,
                name, os):
    '''Updates an existing disk in your image repository.'''
    return azureclient(request).update_disk(disk_name, has_operating_system,
                                            label, media_link,
                                            name, os)


def data_disk_get(request, service_name, deployment_name, role_name, lun):
    """Retrieves the specified data disk from a virtual machine."""
    return azureclient(request).get_data_disk(
        service_name, deployment_name, role_name, lun)


def _get_data_disk_vhd_file_link(request,
                                 service_name,
                                 deployment_name,
                                 role_name,
                                 disk_name):
    """Get the request related vm vhd file storage url."""
    project = next((proj for proj in request.user.authorized_tenants
                    if proj.id == request.user.project_id), None)
    if project:
        cs = azureclient(request).get_hosted_service_properties(service_name)
        storage_account = project.name + STORAGE_ACCOUNTS_SUFFIX[
            cs.hosted_service_properties.location]
        time_stamp = _get_time_stamp()
        vhd_file_blob = DATA_DISK_BLOB_NAME_FORMAT % (deployment_name,
                                                      role_name,
                                                      disk_name,
                                                      time_stamp)
        return CN_STORAGE_BASE_URL % (storage_account,
                                      VHDS_CONTAINER,
                                      vhd_file_blob)


def _get_available_lun_number(instance):
    used_luns = []
    if instance.data_virtual_hard_disks is not None:
        for dv in instance.data_virtual_hard_disks:
            used_luns.append(dv.lun)
    for i in range(0, instance.role.max_data_disk_count):
        if i not in used_luns:
            return i
    return instance.role.max_data_disk_count


def data_disk_attach(request,
                     service_name, deployment_name, role_name,
                     disk_name=None,
                     host_caching=None, media_link=None, disk_label=None,
                     logical_disk_size_in_gb=None,
                     source_media_link=None):
    """Adds a data disk to a virtual machine."""
    client = azureclient(request)
    media_link = _get_data_disk_vhd_file_link(
        request, service_name,
        deployment_name, role_name, disk_name)
    vm = client.get_role(service_name, deployment_name, role_name)
    role_sizes = client.list_role_sizes()
    rolesize_dict = dict([(item.name, item) for item in role_sizes])
    vm.role = rolesize_dict.get(vm.role_size)
    lun = _get_available_lun_number(vm)
    if int(lun) < vm.role.max_data_disk_count:
        result = client.add_data_disk(
            service_name, deployment_name, role_name, lun,
            host_caching, media_link, disk_label,
            disk_name=disk_name,
            logical_disk_size_in_gb=logical_disk_size_in_gb,
            source_media_link=source_media_link)
        return _get_operation_status(client, result.request_id)
    else:
        raise azure_exceptions.AzureException(400,
                                              "Data disk count exceeded.")


def data_disk_reattach(request,
                       service_name, deployment_name, role_name, lun=0,
                       host_caching=None, media_link=None, updated_lun=None,
                       disk_label=None, disk_name=None,
                       logical_disk_size_in_gb=None):
    """Updates the specified data disk attached

    to the specified virtual machine.
    """
    return azureclient(request).update_data_disk(
        service_name, deployment_name, role_name, lun,
        host_caching, media_link, updated_lun,
        disk_label, disk_name,
        logical_disk_size_in_gb)


def data_disk_deattach(request,
                       service_name, deployment_name,
                       role_name, lun=0, delete_vhd=False):
    """Removes the specified data disk from a virtual machine."""
    client = azureclient(request)
    result = client.delete_data_disk(
        service_name, deployment_name, role_name, lun, delete_vhd)
    return _get_operation_status(client, result.request_id)


"""Windows Azure Blob Storage."""


@memoized
def blobclient(account_name, account_key):
    """Windows Azure Blob Storage Service Client."""
    return blobservice.BlobService(account_name=account_name,
                                   account_key=account_key)


def container_create(account_name, account_key, container_name):
    """Create a container."""
    return blobclient(account_name,
                      account_key).create_container(
                          container_name=container_name,
                          fail_on_exist=True)
