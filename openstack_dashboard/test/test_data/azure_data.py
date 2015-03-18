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

import copy

from azure.servicemanagement import AsynchronousOperationResult
from azure.servicemanagement import AttachedTo
from azure.servicemanagement import ComputeCapabilities
from azure.servicemanagement import ConfigurationSet
from azure.servicemanagement import ConfigurationSetInputEndpoint
from azure.servicemanagement import ConfigurationSetInputEndpoints
from azure.servicemanagement import ConfigurationSets
from azure.servicemanagement import DataVirtualHardDisk
from azure.servicemanagement import DataVirtualHardDisks
from azure.servicemanagement import Deployment
from azure.servicemanagement import Deployments
from azure.servicemanagement import Disk
from azure.servicemanagement import HostedService
from azure.servicemanagement import HostedServiceProperties
from azure.servicemanagement import InstanceEndpoint
from azure.servicemanagement import InstanceEndpoints
from azure.servicemanagement import Location
from azure.servicemanagement import Operation
from azure.servicemanagement import OperationError
from azure.servicemanagement import OSImage
from azure.servicemanagement import OSVirtualHardDisk
from azure.servicemanagement import Role
from azure.servicemanagement import RoleInstance
from azure.servicemanagement import RoleInstanceList
from azure.servicemanagement import RoleList
from azure.servicemanagement import RoleSize
from azure.servicemanagement import StorageAccountProperties
from azure.servicemanagement import StorageService
from azure.servicemanagement import Subscription

from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.azure_subscriptions = utils.TestDataContainer()

    TEST.azure_locations = utils.TestDataContainer()
    TEST.azure_rolesizes = utils.TestDataContainer()

    TEST.azure_cloud_services = utils.TestDataContainer()
    TEST.azure_cloud_services_with_deployment = utils.TestDataContainer()

    TEST.azure_roles = utils.TestDataContainer()
    TEST.azure_role_instances = utils.TestDataContainer()

    TEST.azure_deployments = utils.TestDataContainer()

    TEST.azure_os_images = utils.TestDataContainer()

    TEST.azure_endpoints = utils.TestDataContainer()
    TEST.azure_instance_endpoints = utils.TestDataContainer()

    TEST.azure_disks = utils.TestDataContainer()
    TEST.azure_data_disks = utils.TestDataContainer()

    TEST.azure_storage_accounts = utils.TestDataContainer()

    TEST.azure_operation_status = utils.TestDataContainer()

    TEST.azure_async_results = utils.TestDataContainer()

    # Subscriptions
    subscription_1 = Subscription()
    subscription_1.max_hosted_services = 20
    subscription_1.account_admin_live_email_id = \
        'letv_cloud@letv.partner.onmschina.cn'
    subscription_1.max_storage_accounts = 20
    subscription_1.max_dns_servers = 20
    subscription_1.subscription_name = '\u6d4b\u8bd5\u8ba2\u9605-01'
    subscription_1.max_core_count = 100
    subscription_1.aad_tenant_id = '57abbe9c-d183-4a3a-835b-2f0b56971bab'
    subscription_1.max_local_network_sites = 20
    subscription_1.created_time = '2015-01-22T06:11:26Z'
    subscription_1.current_virtual_network_sites = 0
    subscription_1.max_virtual_network_sites = 50
    subscription_1.subscription_status = 'Active'
    subscription_1.current_storage_accounts = 2
    subscription_1.current_core_count = 0
    subscription_1.subscription_id = 'a3b9e639-f53a-4089-b66b-b075c5b805a1'
    subscription_1.current_hosted_services = 1
    subscription_1.service_admin_live_email_id = \
        'letv_cloud@letv.partner.onmschina.cn'

    subscription_2 = Subscription()
    subscription_2.max_hosted_services = 20
    subscription_2.account_admin_live_email_id = \
        'letv_cloud@letv.partner.onmschina.cn'
    subscription_2.max_storage_accounts = 20
    subscription_2.max_dns_servers = 20
    subscription_2.subscription_name = '\u6d4b\u8bd5\u8ba2\u9605-02'
    subscription_2.max_core_count = 100
    subscription_2.aad_tenant_id = '57abbe9c-d183-4a3a-835b-2f0b56971bab'
    subscription_2.max_local_network_sites = 20
    subscription_2.created_time = '2015-01-22T06:12:22Z'
    subscription_2.current_virtual_network_sites = 0
    subscription_2.max_virtual_network_sites = 50
    subscription_2.subscription_status = 'Active'
    subscription_2.current_storage_accounts = 2
    subscription_2.current_core_count = 0
    subscription_2.subscription_id = '0c52e978-6279-40bf-a658-30757d5bdbc5'
    subscription_2.current_hosted_services = 0
    subscription_2.service_admin_live_email_id = \
        'letv_cloud@letv.partner.onmschina.cn'

    TEST.azure_subscriptions.add(subscription_1, subscription_2)

    # Locations
    location1 = Location()
    location1.name = 'China North'
    location1.display_name = 'China North'
    location1.available_services = ['Compute',
                                    'Storage',
                                    'PersistentVMRole',
                                    'HighMemory']
    location1.compute_capabilities = ComputeCapabilities()
    location1.compute_capabilities.virtual_machines_role_sizes = ['1', '2']
    location1.compute_capabilities.web_worker_role_sizes = ['A', 'B']
    TEST.azure_locations.add(location1)

    location2 = Location()
    location2.name = 'China East'
    location2.display_name = 'China East'
    location2.available_services = ['Compute',
                                    'Storage',
                                    'PersistentVMRole',
                                    'HighMemory']
    location2.compute_capabilities = ComputeCapabilities()
    location2.compute_capabilities.virtual_machines_role_sizes = ['3', '4']
    location2.compute_capabilities.web_worker_role_sizes = ['C', 'D']
    TEST.azure_locations.add(location2)

    # Role size
    rolesize_basic_1 = RoleSize()
    rolesize_basic_1.supported_by_web_worker_roles = False
    rolesize_basic_1.memory_in_mb = 768
    rolesize_basic_1.supported_by_virtual_machines = True
    rolesize_basic_1.label = u'Basic_A0 (1 cores, 768 MB)'
    rolesize_basic_1.web_worker_resource_disk_size_in_mb = 0
    rolesize_basic_1.max_data_disk_count = 1
    rolesize_basic_1.cores = 1
    rolesize_basic_1.virtual_machine_resource_disk_size_in_mb = 20480
    rolesize_basic_1.name = 'Basic_A0'
    TEST.azure_rolesizes.add(rolesize_basic_1)

    rolesize_basic_2 = RoleSize()
    rolesize_basic_2.supported_by_web_worker_roles = True
    rolesize_basic_2.memory_in_mb = 14336
    rolesize_basic_2.supported_by_virtual_machines = True
    rolesize_basic_2.label = 'A5 (2 cores, 14336 MB)'
    rolesize_basic_2.web_worker_resource_disk_size_in_mb = 501760
    rolesize_basic_2.max_data_disk_count = 4
    rolesize_basic_2.cores = 2
    rolesize_basic_2.virtual_machine_resource_disk_size_in_mb = 138240
    rolesize_basic_2.name = 'A5'
    TEST.azure_rolesizes.add(rolesize_basic_2)

    # Cloud Service
    cloudservice_1 = HostedService()
    cloudservice_1.url = 'https://sha.management.core.chinacloudapi.cn' \
                         '/a3b9e639-f53a-4089-b66b-b075c5b805a1/services' \
                         '/hostedservices/letvcloudservicetest01'
    cloudservice_1.service_name = 'letvcloudservicetest01'
    cloudservice_1.deployments = None
    cloudservice_1.hosted_service_properties = HostedServiceProperties()
    cloudservice_1.hosted_service_properties.status = 'Created'
    cloudservice_1.hosted_service_properties.description = \
        'letv cloud service test 01'
    cloudservice_1.hosted_service_properties.label = 'letvcloudservicetest01'
    cloudservice_1.hosted_service_properties.location = 'China North'
    cloudservice_1.hosted_service_properties.affinity_group = ''
    cloudservice_1.hosted_service_properties.date_created = \
        '2015-02-10T08:18:35Z'
    cloudservice_1.hosted_service_properties.extended_properties = {}
    cloudservice_1.hosted_service_properties.date_last_modified = \
        '2015-02-10T08:18:35Z'
    TEST.azure_cloud_services.add(cloudservice_1)

    cloudservice_2 = HostedService()
    cloudservice_2.url = 'https://sha.management.core.chinacloudapi.cn/' \
                         'a3b9e639-f53a-4089-b66b-b075c5b805a1/services/' \
                         'hostedservices/letvcloudservicetest02'
    cloudservice_2.service_name = 'letvcloudservicetest02'
    cloudservice_2.deployments = None
    cloudservice_2.hosted_service_properties = HostedServiceProperties()
    cloudservice_2.hosted_service_properties.status = 'Created'
    cloudservice_2.hosted_service_properties.description = \
        'letv cloud service test 02'
    cloudservice_2.hosted_service_properties.label = 'letvcloudservicetest02'
    cloudservice_2.hosted_service_properties.location = 'China North'
    cloudservice_2.hosted_service_properties.affinity_group = ''
    cloudservice_2.hosted_service_properties.date_created = \
        '2015-02-10T08:18:51Z'
    cloudservice_2.hosted_service_properties.extended_properties = {}
    cloudservice_2.hosted_service_properties.date_last_modified = \
        '2015-02-10T08:18:52Z'
    TEST.azure_cloud_services.add(cloudservice_2)

    # Cloud Services 01 with deployment
    cs_with_deployment_1 = copy.deepcopy(cloudservice_1)
    cs_with_deployment_1.deployments = Deployments()

    # A 'Production' deployment
    deployment_1 = Deployment()
    deployment_1.status = 'Running'
    deployment_1.private_id = '44320d2d83d5409bbe8a35f1553f0b9f'
    deployment_1.deployment_slot = 'Production'
    deployment_1.locked = False
    deployment_1.name = 'letvcloudservicetest01'
    deployment_1.last_modified_time = ''
    deployment_1.url = 'http://letvcloudservicetest01.chinacloudapp.cn/'
    deployment_1.upgrade_domain_count = '1'
    deployment_1.virtual_network_name = ''
    deployment_1.label = 'testvm01linux'
    deployment_1.input_endpoint_list = None
    deployment_1.sdk_version = ''
    deployment_1.upgrade_status = None
    deployment_1.created_time = '2015-02-10T08:30:47Z'
    deployment_1.persistent_vm_downtime_info = None
    deployment_1.configuration = '<ServiceConfiguration xmlns:xsd="http://' \
                                 'www.w3.org/2001/XMLSchema" xmlns:xsi="http:' \
                                 '//www.w3.org/2001/XMLSchema-instance" ' \
                                 'xmlns="http://schemas.microsoft.com/' \
                                 'ServiceHosting/2008/10/ServiceConfiguration' \
                                 '">\r\n  <Role name="testvm01linux">\r\n    ' \
                                 '<Instances count="1" />\r\n  </Role>\r\n' \
                                 '</ServiceConfiguration>'
    deployment_1.rollback_allowed = False
    deployment_1.extended_properties = {}
    deployment_1.role_list = RoleList()

    # A Linux role
    role_1 = Role()
    role_1.default_win_rm_certificate_thumbprint = ''
    role_1.availability_set_name = ''
    role_1.role_size = 'Basic_A0'
    role_1.os_version = ''
    role_1.role_name = 'testvm01linux'
    role_1.role_type = 'PersistentVMRole'

    role_1.configuration_sets = ConfigurationSets()

    cfg_set_1 = ConfigurationSet()
    cfg_set_1.subnet_names = []
    cfg_set_1.configuration_set_type = 'NetworkConfiguration'
    cfg_set_1.public_ips = None
    cfg_set_1.role_type = ''

    cfg_set_1.input_endpoints = ConfigurationSetInputEndpoints()
    endpoint_dict_1 = {'name': 'SSH',
                       'protocol': 'tcp',
                       'port': 10022,
                       'local_port': 22,
                       'load_balanced_endpoint_set_name': '',
                       'enable_direct_server_return': False,
                       'idle_timeout_in_minutes': 4}
    endpoint_1 = ConfigurationSetInputEndpoint(**endpoint_dict_1)
    endpoint_1.load_balancer_probe = None
    cfg_set_1.input_endpoints.input_endpoints.append(endpoint_1)

    role_1.configuration_sets.configuration_sets.append(cfg_set_1)

    os_vdisk_dict_1 = {
        'source_image_name':
            'b549f4301d0b4295b8e76ceb65df47d4'
            '__Ubuntu-14_10-amd64-server-20141022.3-en-us-30GB',
        'media_link':
            'https://adminchinanorth.blob.core.chinacloudapi.cn'
            '/vhds/letvcloudservicetest01-testvm01linux-sys-disk.vhd',
        'host_caching': 'ReadOnly',
        'disk_label': None,
        'disk_name': 'letvcloudservicetest01-'
                     'testvm01linux-0-201502100830490728',
        'os': 'Linux',
        'remote_source_image_link': None}
    role_1.os_virtual_hard_disk = OSVirtualHardDisk(**os_vdisk_dict_1)

    role_1.data_virtual_hard_disks = DataVirtualHardDisks()
    # Add a data disk for linux vm
    linux_data_disk_1 = DataVirtualHardDisk()
    linux_data_disk_1.logical_disk_size_in_gb = 1
    linux_data_disk_1.media_link = \
        'https://adminchinanorth.blob.core.chinacloudapi.cn/vhds/' \
        'letvcloudservicetest01-testvm01linux-data-disk.vhd'
    linux_data_disk_1.disk_name = \
        'letvcloudservicetest01-testvm01linux-0-201502120658120720'
    role_1.data_virtual_hard_disks.data_virtual_hard_disks.append(
        linux_data_disk_1)

    deployment_1.role_list.roles.append(role_1)

    deployment_1.role_instance_list = RoleInstanceList()
    role_instance_1 = RoleInstance()
    role_instance_1.instance_upgrade_domain = 0
    role_instance_1.instance_size = 'Basic_A0'
    role_instance_1.fqdn = ''
    role_instance_1.instance_fault_domain = 0
    role_instance_1.instance_name = 'testvm01linux'
    role_instance_1.public_ips = None
    role_instance_1.role_name = 'testvm01linux'
    role_instance_1.host_name = 'letvcloudservicetest01'
    role_instance_1.power_state = 'Started'
    role_instance_1.instance_error_code = ''
    role_instance_1.ip_address = '10.207.16.108'
    role_instance_1.instance_status = 'ReadyRole'
    role_instance_1.instance_state_details = ''

    role_instance_1.instance_endpoints = InstanceEndpoints()

    ins_endpoint_1 = InstanceEndpoint()
    ins_endpoint_1.protocol = 'tcp'
    ins_endpoint_1.vip = '42.159.83.84'
    ins_endpoint_1.public_port = 10022
    ins_endpoint_1.name = 'SSH'
    ins_endpoint_1.local_port = 22
    role_instance_1.instance_endpoints.instance_endpoints.append(
        ins_endpoint_1)

    deployment_1.role_instance_list.role_instances.append(role_instance_1)

    cs_with_deployment_1.deployments.deployments.append(deployment_1)
    TEST.azure_cloud_services_with_deployment.add(cs_with_deployment_1)

    # Cloud Services 02 with deployment
    cs_with_deployment_2 = copy.deepcopy(cloudservice_2)
    cs_with_deployment_2.deployments = Deployments()

    # A 'Production' deployment
    deployment_2 = Deployment()
    deployment_2.status = 'Running'
    deployment_2.private_id = 'fda6063f76414ed8883d35f23613d34b'
    deployment_2.deployment_slot = 'Production'
    deployment_2.locked = False
    deployment_2.name = 'letvcloudservicetest02'
    deployment_2.last_modified_time = ''
    deployment_2.url = 'http://letvcloudservicetest02.chinacloudapp.cn/'
    deployment_2.upgrade_domain_count = '1'
    deployment_2.virtual_network_name = ''
    deployment_2.label = 'testvm02win'
    deployment_2.input_endpoint_list = None
    deployment_2.sdk_version = ''
    deployment_2.upgrade_status = None
    deployment_2.created_time = '2015-02-10T10:05:40Z'
    deployment_2.persistent_vm_downtime_info = None
    deployment_2.configuration = \
        '<ServiceConfiguration xmlns:xsd="http://www.w3.org/2001/XMLSchema' \
        '" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="ht' \
        'tp://schemas.microsoft.com/ServiceHosting/2008/10/ServiceConfigur' \
        'ation">\r\n  <Role name="testvm01linux">\r\n    <Instances count=' \
        '"1" />\r\n  </Role>\r\n</ServiceConfiguration>'
    deployment_2.rollback_allowed = False
    deployment_2.extended_properties = {}
    deployment_2.role_list = RoleList()

    # A windows role
    role_2 = Role()
    role_2.default_win_rm_certificate_thumbprint = \
        '25B0A0DF6C5A911957B6670B5E68F0894335703C'
    role_2.availability_set_name = ''
    role_2.role_size = 'A5'
    role_2.os_version = ''
    role_2.role_name = 'testvm02win'
    role_2.role_type = 'PersistentVMRole'

    role_2.configuration_sets = ConfigurationSets()

    cfg_set_2 = ConfigurationSet()
    cfg_set_2.subnet_names = []
    cfg_set_2.configuration_set_type = 'NetworkConfiguration'
    cfg_set_2.public_ips = None
    cfg_set_2.role_type = ''
    cfg_set_2.input_endpoints = ConfigurationSetInputEndpoints()

    endpoint_dict_2 = {'name': 'PowerShell',
                       'protocol': 'tcp',
                       'port': 5986,
                       'local_port': 5986,
                       'load_balanced_endpoint_set_name': '',
                       'enable_direct_server_return': False,
                       'idle_timeout_in_minutes': 4}
    endpoint_2 = ConfigurationSetInputEndpoint(**endpoint_dict_2)
    endpoint_2.load_balancer_probe = None
    cfg_set_2.input_endpoints.input_endpoints.append(endpoint_2)

    endpoint_dict_3 = {'name': 'Remote Desktop',
                       'protocol': 'tcp',
                       'port': 52234,
                       'local_port': 3389,
                       'load_balanced_endpoint_set_name': '',
                       'enable_direct_server_return': False,
                       'idle_timeout_in_minutes': 4}
    endpoint_3 = ConfigurationSetInputEndpoint(**endpoint_dict_3)
    endpoint_3.load_balancer_probe = None
    cfg_set_2.input_endpoints.input_endpoints.append(endpoint_3)

    role_2.configuration_sets.configuration_sets.append(cfg_set_2)

    os_vdisk_dict_2 = {
        'source_image_name': '0c5c79005aae478e8883bf950a861ce0'
                             '__Windows-Server-2012-Essentials-20141204-enus',
        'media_link': 'https://adminchinaeast.blob.core.chinacloudapi.cn/vhds'
                      '/letvcloudservicetest02-testvm02win-sys-disk.vhd',
        'host_caching': 'ReadWrite',
        'disk_label': None,
        'disk_name': 'letvcloudservicetest02-testvm02win-0-201502101005430932',
        'os': 'Windows',
        'remote_source_image_link': None}
    role_2.os_virtual_hard_disk = OSVirtualHardDisk(**os_vdisk_dict_2)

    # role has no data disk
    role_2.data_virtual_hard_disks = DataVirtualHardDisks()
    role_2.data_virtual_hard_disks.data_virtual_hard_disks = []

    deployment_2.role_list.roles.append(role_2)

    deployment_2.role_instance_list = RoleInstanceList()
    role_instance_2 = RoleInstance()
    role_instance_2.instance_upgrade_domain = 0
    role_instance_2.instance_size = 'A5'
    role_instance_2.fqdn = ''
    role_instance_2.instance_fault_domain = 0
    role_instance_2.instance_name = 'testvm02win'
    role_instance_2.public_ips = None
    role_instance_2.role_name = 'testvm02win'
    role_instance_2.host_name = ''
    role_instance_2.power_state = 'Started'
    role_instance_2.instance_error_code = ''
    role_instance_2.ip_address = '10.204.202.21'
    role_instance_2.instance_status = 'ReadyRole'
    role_instance_2.instance_state_details = ''

    role_instance_2.instance_endpoints = InstanceEndpoints()

    ins_endpoint_2 = InstanceEndpoint()
    ins_endpoint_2.protocol = 'tcp'
    ins_endpoint_2.vip = '42.159.142.39'
    ins_endpoint_2.public_port = 5986
    ins_endpoint_2.name = 'PowerShell'
    ins_endpoint_2.local_port = 5986
    role_instance_2.instance_endpoints.instance_endpoints.append(
        ins_endpoint_2)

    ins_endpoint_3 = InstanceEndpoint()
    ins_endpoint_3.protocol = 'tcp'
    ins_endpoint_3.vip = '42.159.142.39'
    ins_endpoint_3.public_port = 52234
    ins_endpoint_3.name = 'Remote Desktop'
    ins_endpoint_3.local_port = 3389
    role_instance_2.instance_endpoints.instance_endpoints.append(
        ins_endpoint_3)

    deployment_2.role_instance_list.role_instances.append(role_instance_2)

    cs_with_deployment_2.deployments.deployments.append(deployment_2)
    TEST.azure_cloud_services_with_deployment.add(cs_with_deployment_2)

    TEST.azure_roles.add(role_1, role_2)
    TEST.azure_role_instances.add(role_instance_1, role_instance_2)
    TEST.azure_deployments.add(deployment_1, deployment_2)
    TEST.azure_instance_endpoints.add(ins_endpoint_1,
                                      ins_endpoint_2,
                                      ins_endpoint_3)
    TEST.azure_endpoints.add(endpoint_1, endpoint_2, endpoint_3)

    # OS Images
    os_img_linux_1 = OSImage()
    os_img_linux_1.pricing_detail_link = ''
    os_img_linux_1.eula = \
        'http://www.ubuntu.com/project/about-ubuntu/licensing;' \
        'http://www.ubuntu.com/aboutus/privacypolicy'
    os_img_linux_1.is_premium = False
    os_img_linux_1.publisher_name = 'Canonical'
    os_img_linux_1.category = 'Public'
    os_img_linux_1.icon_uri = 'Ubuntu-cof-100.png'
    os_img_linux_1.label = 'Ubuntu Server 14.10'
    os_img_linux_1.show_in_gui = True
    os_img_linux_1.location = 'China East;China North'
    os_img_linux_1.recommended_vm_size = ''
    os_img_linux_1.description = "This is ubuntu description."
    os_img_linux_1.os_state = ''
    os_img_linux_1.image_family = 'Ubuntu Server 14.10'
    os_img_linux_1.logical_size_in_gb = 30
    os_img_linux_1.affinity_group = ''
    os_img_linux_1.privacy_uri = 'http://www.ubuntu.com/aboutus/privacypolicy'
    os_img_linux_1.name = \
        'b549f4301d0b4295b8e76ceb65df47d4__' \
        'Ubuntu-14_10-amd64-server-20141022.3-en-us-30GB'
    os_img_linux_1.language = ''
    os_img_linux_1.small_icon_uri = 'Ubuntu-cof-45.png'
    os_img_linux_1.published_date = '2014-10-23T00:00:00Z'
    os_img_linux_1.os = 'Linux'
    os_img_linux_1.media_link = ''

    os_img_windows_2 = OSImage()
    os_img_windows_2.pricing_detail_link = ''
    os_img_windows_2.eula = '',
    os_img_windows_2.is_premium = False
    os_img_windows_2.publisher_name = \
        'Microsoft Windows Server Essentials Group'
    os_img_windows_2.category = 'Public'
    os_img_windows_2.icon_uri = 'WindowsServer2012R2_100.png'
    os_img_windows_2.label = 'Windows Server Essentials Experience on' \
                             ' Windows Server 2012 R2 (en-us)'
    os_img_windows_2.show_in_gui = True
    os_img_windows_2.location = 'China East;China North'
    os_img_windows_2.recommended_vm_size = ''
    os_img_windows_2.description = 'This is windows description.'
    os_img_windows_2.os_state = ''
    os_img_windows_2.image_family = 'Windows Server Essentials Experience' \
                                    ' on Windows Server 2012 R2 (en-us)'
    os_img_windows_2.logical_size_in_gb = 127
    os_img_windows_2.affinity_group = ''
    os_img_windows_2.privacy_uri = ''
    os_img_windows_2.name = \
        '0c5c79005aae478e8883bf950a861ce0' \
        '__Windows-Server-2012-Essentials-20141204-enus'
    os_img_windows_2.language = ''
    os_img_windows_2.small_icon_uri = 'WindowsServer2012R2_45.png'
    os_img_windows_2.published_date = '2014-12-03T16:00:00Z'
    os_img_windows_2.os = 'Windows'
    os_img_windows_2.media_link = ''

    TEST.azure_os_images.add(os_img_linux_1, os_img_windows_2)

    # System Disks
    os_disk_linux_1 = Disk()
    os_disk_linux_1.has_operating_system = ''
    os_disk_linux_1.logical_disk_size_in_gb = 30
    os_disk_linux_1.name = \
        'letvcloudservicetest01-testvm01linux-0-201502110913560438'
    os_disk_linux_1.is_corrupted = ''
    os_disk_linux_1.label = ''
    os_disk_linux_1.location = 'China North'
    os_disk_linux_1.affinity_group = ''
    os_disk_linux_1.source_image_name = \
        'b549f4301d0b4295b8e76ceb65df47d4__' \
        'Ubuntu-14_10-amd64-server-20141022.3-en-us-30GB'
    os_disk_linux_1.os = 'Linux'
    os_disk_linux_1.media_link = \
        'https://adminchinanorth.blob.core.chinacloudapi' \
        '.cn/vhds/letvcloudservicetest01-testvm01linux-sys-disk.vhd'
    os_attach_1 = AttachedTo()
    os_attach_1.hosted_service_name = 'letvcloudservicetest01',
    os_attach_1.role_name = 'testvm01linux',
    os_attach_1.deployment_name = 'letvcloudservicetest01'
    os_disk_linux_1.attached_to = os_attach_1

    os_disk_windows_2 = Disk()
    os_disk_windows_2.has_operating_system = ''
    os_disk_windows_2.logical_disk_size_in_gb = 127
    os_disk_windows_2.name = \
        'letvcloudservicetest02-testvm02win-0-201502101005430932'
    os_disk_windows_2.is_corrupted = ''
    os_disk_windows_2.label = ''
    os_disk_windows_2.location = 'China East'
    os_disk_windows_2.affinity_group = ''
    os_disk_windows_2.source_image_name = \
        '0c5c79005aae478e8883bf950a861ce0' \
        '__Windows-Server-2012-Essentials-20141204-enus'
    os_disk_windows_2.os = 'Windows'
    os_disk_windows_2.media_link = \
        'https://adminchinaeast.blob.core.chinacloudapi.cn/vhds' \
        '/letvcloudservicetest02-testvm02win-sys-disk.vhd'
    os_attach_2 = AttachedTo()
    os_attach_2.hosted_service_name = 'letvcloudservicetest02',
    os_attach_2.role_name = 'testvm02win',
    os_attach_2.deployment_name = 'letvcloudservicetest02'
    os_disk_linux_1.attached_to = os_attach_2

    TEST.azure_disks.add(os_disk_linux_1, os_disk_windows_2)

    # Data Disks
    data_disk_1_attached = Disk()
    data_disk_1_attached.has_operating_system = ''
    data_disk_1_attached.logical_disk_size_in_gb = 1
    data_disk_1_attached.name = \
        'letvcloudservicetest01-testvm01linux-0-201502120353540526'
    data_disk_1_attached.is_corrupted = ''
    data_disk_1_attached.label = ''
    data_disk_1_attached.location = 'China North'
    data_disk_1_attached.affinity_group = ''
    data_disk_1_attached.source_image_name = ''
    data_disk_1_attached.os = ''
    data_disk_1_attached.media_link = 'https://adminchinanorth.blob.core.' \
                                      'chinacloudapi.cn/vhds/datadisk01.vhd'
    data_attach_1 = AttachedTo()
    data_attach_1.hosted_service_name = 'letvcloudservicetest01',
    data_attach_1.role_name = 'testvm01linux',
    data_attach_1.deployment_name = 'letvcloudservicetest01'
    data_disk_1_attached.attached_to = data_attach_1

    data_disk_2_free = Disk()
    data_disk_2_free.has_operating_system = ''
    data_disk_2_free.logical_disk_size_in_gb = 1
    data_disk_2_free.name = \
        'letvcloudservicetest01-testvm01linux-0-201502120353540666'
    data_disk_2_free.is_corrupted = ''
    data_disk_2_free.label = ''
    data_disk_2_free.location = 'China North'
    data_disk_2_free.affinity_group = ''
    data_disk_2_free.source_image_name = ''
    data_disk_2_free.os = ''
    data_disk_2_free.media_link = 'https://adminchinanorth.blob.core' \
                                  '.chinacloudapi.cn/vhds/datadisk02.vhd'
    data_disk_2_free.attached_to = None

    TEST.azure_data_disks.add(data_disk_1_attached, data_disk_2_free)

    storage_account_1 = StorageService()
    storage_account_1.storage_service_keys = None
    storage_account_1.url = \
        'https://sha.management.core.chinacloudapi.cn/' \
        'a3b9e639-f53a-4089-b66b-b075c5b805a1/services/' \
        'storageservices/adminchinanorth'
    storage_account_1.service_name = 'adminchinanorth'
    storage_account_1.capabilities = None
    storage_account_1.extended_properties = {}

    s_properties_1 = StorageAccountProperties()
    s_properties_1.status = 'Created'
    s_properties_1.account_type = 'Standard_LRS'
    s_properties_1.description = ''
    s_properties_1.geo_secondary_region = ''
    s_properties_1.creation_time = '2015-02-09T05:27:21Z'
    s_properties_1.geo_primary_region = 'China North'
    s_properties_1.label = 'adminchinanorth'
    s_properties_1.status_of_primary = 'Available'
    s_properties_1.location = 'China North'
    s_properties_1.affinity_group = ''
    s_properties_1.last_geo_failover_time = ''
    s_properties_1.status_of_secondary = ''
    s_properties_1.endpoints = [
        'https://adminchinanorth.blob.core.chinacloudapi.cn/',
        'https://adminchinanorth.queue.core.chinacloudapi.cn/',
        'https://adminchinanorth.table.core.chinacloudapi.cn/',
        'https://adminchinanorth.file.core.chinacloudapi.cn/']
    s_properties_1.geo_replication_enabled = False
    storage_account_1.storage_service_properties = s_properties_1

    storage_account_2 = StorageService()
    storage_account_2.storage_service_keys = None
    storage_account_2.url = \
        'https://sha.management.core.chinacloudapi.cn/' \
        'a3b9e639-f53a-4089-b66b-b075c5b805a1/services/' \
        'storageservices/adminchinaeast'
    storage_account_2.service_name = 'adminchinaeast'
    storage_account_2.capabilities = None
    storage_account_2.extended_properties = {}

    s_properties_2 = StorageAccountProperties()
    s_properties_2.status = 'Created'
    s_properties_2.account_type = 'Standard_LRS'
    s_properties_2.description = ''
    s_properties_2.geo_secondary_region = ''
    s_properties_2.creation_time = '2015-02-09T05:27:10Z'
    s_properties_2.geo_primary_region = 'China East'
    s_properties_2.label = 'adminchinaeast'
    s_properties_2.status_of_primary = 'Available'
    s_properties_2.location = 'China East'
    s_properties_2.affinity_group = ''
    s_properties_2.last_geo_failover_time = ''
    s_properties_2.status_of_secondary = ''
    s_properties_2.endpoints = [
        'https://adminchinaeast.blob.core.chinacloudapi.cn/',
        'https://adminchinaeast.queue.core.chinacloudapi.cn/',
        'https://adminchinaeast.table.core.chinacloudapi.cn/',
        'https://adminchinaeast.file.core.chinacloudapi.cn/']
    s_properties_2.geo_replication_enabled = False
    storage_account_2.storage_service_properties = s_properties_2

    TEST.azure_storage_accounts.add(storage_account_1, storage_account_2)

    operation_success = Operation()
    operation_success.id = '1'
    operation_success.status = 'Succeeded'
    operation_success.http_status_code = '200'

    operation_failed = Operation()
    operation_failed.id = '2'
    operation_failed.status = 'Failed'
    operation_failed.http_status_code = '400'
    op_error = OperationError()
    op_error.code = '400'
    op_error.message = 'Bad Request'
    operation_failed.error = op_error

    operation_inprogress = Operation()
    operation_inprogress.id = '3'
    operation_inprogress.status = 'InProgress'
    operation_inprogress.http_status_code = '102'
    op_processing = OperationError()
    op_processing.code = '102'
    op_processing.message = 'Processing'
    operation_inprogress.error = op_processing

    TEST.azure_operation_status.add(operation_success,
                                    operation_failed,
                                    operation_inprogress)

    azure_async_results = AsynchronousOperationResult('1')
    TEST.azure_async_results.add(azure_async_results)
