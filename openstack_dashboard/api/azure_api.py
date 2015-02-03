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

import os
import uuid

import random

import logging

from azure.servicemanagement import ConfigurationSet  # noqa
from azure.servicemanagement import ConfigurationSetInputEndpoint  # noqa
from azure.servicemanagement import LinuxConfigurationSet  # noqa
from azure.servicemanagement import OSVirtualHardDisk  # noqa
from azure.servicemanagement import servicemanagementservice as sms
from azure.servicemanagement import WindowsConfigurationSet  # noqa

from django.conf import settings

from horizon.utils.memoized import memoized  # noqa

LOG = logging.getLogger(__name__)

AZURE_MANAGEMENT_HOST = getattr(settings,
                                'AZURE_MANAGEMENT_HOST',
                                # Default China
                                'management.core.chinacloudapi.cn')

CN_STORAGE_BASE_URL = 'https://%s.blob.core.chinacloudapi.cn/%s/%s'

AZURE_KEY_FILE_FOLDER = getattr(
    settings, 'AZURE_KEY_FILE_FOLDER',
    # getattr(settings, 'ROOT_PATH', ''),
    '/home/yulong/azure_keys/test/test_1')

# subscription_id='a3b9e639-f53a-4089-b66b-b075c5b805a1'
# cert_file='/home/yulong/azure_keys/mycert.pem'


def create_new_key_for_subscription(project_id):
    """Create a new rsa key file for a tenant/subscription."""
    # use namespace to make sure each tenant_name has a constant uuid
    key_id = uuid.uuid3(uuid.NAMESPACE_X500, project_id)
    KEY_PEM = "%s/%s.pem" % (AZURE_KEY_FILE_FOLDER, key_id)
    KEY_CER = "%s/%s.cer" % (AZURE_KEY_FILE_FOLDER, key_id)
    os.system('openssl req -x509 -nodes'
              ' -days 365 -newkey rsa:1024'
              ' -keyout %s -out %s'
              ' -subj "/CN=%s"' % (KEY_PEM, KEY_PEM, project_id))
    os.system('openssl x509 -inform pem'
              ' -in %s -outform der -out %s' % (KEY_PEM, KEY_CER))


def get_tenant_pem_file_path(project_id):
    """Get the tenant cert pem file absolute path."""
    key_id = uuid.uuid3(uuid.NAMESPACE_X500, str(project_id))
    return "%s/%s.pem" % (AZURE_KEY_FILE_FOLDER, key_id)


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
def location_list(request):
    """Azure location geographic domain."""
    return azureclient(request).list_locations()


@memoized
def cloud_service_list(request):
    """Get all Azure Cloud Services of the subscription."""
    return azureclient(request).list_hosted_services()


def cloud_service_delete(request, service_name):
    """Delete a cloud service."""
    return azureclient(request).delete_hosted_service(service_name)


@memoized
def storage_account_list(request):
    """Get all Azure storage accounts of the subscription."""
    return azureclient(request).list_storage_accounts()


@memoized
def affinity_group_list(request):
    """Get all Azure affinity group of the subscription."""
    return azureclient(request).list_affinity_groups()


@memoized
def cloud_service_detail(request, service_name, embed_detail=False):
    """Get details of one specific cloud service."""
    return azureclient(request).get_hosted_service_properties(
        service_name=service_name,
        embed_detail=embed_detail)


@memoized
def role_size_list(request):
    """Get the list of available VM sizes (role sizes)."""
    return azureclient(request).list_role_sizes()


@memoized
def get_deployment_by_name(request, service_name, deployment_name):
    """Get deployment by name."""
    return azureclient(request).get_deployment_by_name(service_name,
                                                       deployment_name)


def create_deployment(request,
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


def delete_deployment(request, service_name, deployment_name):
    """Delete a azure deployment."""
    return azureclient(request).delete_deployment(service_name,
                                                  deployment_name)


@memoized
def list_operating_systems(request):
    """Lists the versions of the guest operating system."""
    return azureclient(request).list_operating_systems()


@memoized
def list_os_images(request):
    """Get the list of available images."""
    return azureclient(request).list_os_images()


@memoized
def list_operating_system_families(request):
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
                for endpoint in conf.input_endpoints:
                    public_ports.append(endpoint.port)
    public_ports.sort()
    return public_ports


def virtual_machine_get(request, service_name,
                        deployment_name, role_name):
    """Get the detail of an instance."""
    return azureclient(request).get_role(service_name,
                                         deployment_name,
                                         role_name)


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
                           deployment_slot='production',
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
            computer_name=deployment_name,
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
            host_name=deployment_name,
            user_name=admin_username,
            user_password=user_password,
            disable_ssh_password_authentication=False)
        if enable_port:
            network_config = _create_linux_ssh_endpoint()

    new_os_sys_disk_url = '%s-%s-sys-disk.vhd' % (deployment_name, role_name)
    osvhd = OSVirtualHardDisk(
        source_image_name=image_name,
        media_link=CN_STORAGE_BASE_URL % ('myvhdsaccount',
                                          'vhds',
                                          new_os_sys_disk_url),
        # caching mode of the operating system disk
        # all default 'ReadOnly'
        host_caching='ReadOnly')

    if create_new_cloudservice:
        # Create a new cloud service and a deployment for this new vm
        client.create_hosted_service(
            service_name=service_name,
            label=service_name,
            location=location)
        return client.create_virtual_machine_deployment(
            service_name=service_name,
            deployment_name=deployment_name,
            deployment_slot=deployment_slot,
            label=label,
            role_name=role_name,
            system_config=conf,
            os_virtual_hard_disk=osvhd,
            network_config=network_config,
            role_size=role_size)
    else:
        # Add this new vm to the existing cloud-service/deployment
        cs = client.get_hosted_service_properties(
            service_name=service_name,
            embed_detail=True)
        if enable_port and cs.deployments:
            public_ports = _get_cloudservice_used_public_ports(cs)
            # Random a new public port in the existing cloud service
            for endpoint in network_config.input_endpoints.input_endpoints:
                new_port = random.randint(int(public_ports[-1]),
                                          int(public_ports[-1]) + 10)
                endpoint.port = str(new_port)
                public_ports.append(str(new_port))
            return client.add_role(
                service_name=service_name,
                deployment_name=deployment_name,
                role_name=role_name,
                system_config=conf,
                os_virtual_hard_disk=osvhd,
                network_config=network_config,
                role_size=role_size)
        else:
            return client.create_virtual_machine_deployment(
                service_name=service_name,
                deployment_name=deployment_name,
                deployment_slot=deployment_slot,
                label=label,
                role_name=role_name,
                system_config=conf,
                os_virtual_hard_disk=osvhd,
                network_config=network_config,
                role_size=role_size)


def virtual_machine_delete(request, service_name,
                           deployment_name, role_name):
    """Delete an azure virtual of a cloudservice/deployment."""
    return azureclient(request).delete_role(
        service_name=service_name,
        deployment_name=deployment_name,
        role_name=role_name)


def virtual_machine_shutdown(request, service_name,
                             deployment_name, role_name,
                             post_shutdown_action='Stopped'):
    """Shutdown an azure vm of a cloudservice/deployment."""
    return azureclient(request).shutdown_role(
        service_name=service_name,
        deployment_name=deployment_name,
        role_name=role_name,
        post_shutdown_action=post_shutdown_action)


def virtual_machine_restart(request, service_name, deployment_name, role_name):
    """Start an azure vm of a cloudservice/deployment."""
    return azureclient(request).restart_role(service_name,
                                             deployment_name,
                                             role_name)


def virtual_machine_start(request, service_name, deployment_name, role_name):
    """Start an azure vm of a cloudservice/deployment."""
    return azureclient(request).start_role(service_name,
                                           deployment_name,
                                           role_name)


def virtual_machine_capture(request, service_name, deployment_name,
                            role_name, post_capture_action,
                            target_image_name, target_image_label,
                            provisioning_configuration=None):
    """captures a virtual machine image to your image gallery."""
    return azureclient(request).capture_role(
        service_name, deployment_name, role_name,
        post_capture_action, target_image_name, target_image_label,
        provisioning_configuration)


def virtual_machine_resize(request, service_name,
                           deployment_name, role_name,
                           role_size):
    """Resize an azure virtual machine."""
    return azureclient(request).update_role(
        service_name, deployment_name,
        role_name,
        role_size=role_size)


def virtual_machine_update(request, service_name, deployment_name, role_name,
                           os_virtual_hard_disk=None, network_config=None,
                           availability_set_name=None,
                           data_virtual_hard_disks=None,
                           role_size=None, role_type='PersistentVMRole',
                           resource_extension_references=None,
                           provision_guest_agent=None):
    """Update an azure virtual machine."""
    return azureclient(request).update_role(
        service_name, deployment_name, role_name,
        os_virtual_hard_disk, network_config,
        availability_set_name, data_virtual_hard_disks,
        role_size, role_type,
        resource_extension_references,
        provision_guest_agent)
