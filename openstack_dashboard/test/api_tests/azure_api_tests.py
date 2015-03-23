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

from azure import servicemanagement as smng

from mock import patch
from mock import PropertyMock

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class AzureApiTests(test.APITestCase):
    def test_subscription_get(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65

            subscription = self.azure_subscriptions.first()
            azureclient = self.stub_azureclient()
            azureclient.get_subscription().AndReturn(subscription)
            self.mox.ReplayAll()
            subs = api.azure_api.subscription_get(self.request)
            self.assertIsInstance(subs, smng.Subscription)

    def test_location_list(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_locations = self.azure_locations.list()
            azureclient = self.stub_azureclient()
            azureclient.list_locations().AndReturn(api_locations)
            self.mox.ReplayAll()

            locations = api.azure_api.location_list(self.request)
            self.assertEqual(len(locations), 2)

    def test_cloud_service_list(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservices = self.azure_cloud_services.list()
            azureclient = self.stub_azureclient()
            azureclient.list_hosted_services().AndReturn(api_cloudservices)
            self.mox.ReplayAll()

            cloudservices = api.azure_api.cloud_service_list(self.request)
            self.assertEqual(len(cloudservices), 2)

    def test_cloud_service_detail(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = \
                self.azure_cloud_services_with_deployment.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                service_name=api_cloudservice.service_name,
                embed_detail=True).AndReturn(api_cloudservice)
            self.mox.ReplayAll()

            cloudservice = api.azure_api.cloud_service_detail(
                self.request,
                api_cloudservice.service_name,
                True)
            self.assertIsInstance(cloudservice, smng.HostedService)
            self.assertIsNotNone(cloudservice.deployments)
            self.assertIsInstance(cloudservice.deployments, smng.Deployments)

    def test_cloud_service_delete(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            azureclient = self.stub_azureclient()
            azureclient.delete_hosted_service(api_cloudservice.service_name)
            self.mox.ReplayAll()

            ret = api.azure_api.cloud_service_delete(
                self.request,
                api_cloudservice.service_name)
            # Request Accept 202
            self.assertIsNone(ret)

    def test_cloud_service_create(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            azureclient = self.stub_azureclient()
            azureclient.create_hosted_service(
                api_cloudservice.service_name,
                api_cloudservice.hosted_service_properties.label,
                None,
                api_cloudservice.hosted_service_properties.location,
                None, None)
            self.mox.ReplayAll()

            ret = api.azure_api.cloud_service_create(
                self.request,
                service_name=api_cloudservice.service_name,
                label=api_cloudservice.hosted_service_properties.label,
                location=api_cloudservice.hosted_service_properties.location)

            self.assertTrue(ret)

    def test_storage_account_list(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_storages = self.azure_storage_accounts.list()
            azureclient = self.stub_azureclient()
            azureclient.list_storage_accounts().AndReturn(api_storages)
            self.mox.ReplayAll()

            storages = api.azure_api.storage_account_list(self.request)
            self.assertEqual(len(storages), 2)
            for s in storages:
                self.assertIsInstance(s, smng.StorageService)

    def test_storage_account_create(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_storage = self.azure_storage_accounts.first()
            azureclient = self.stub_azureclient()
            azureclient.create_storage_account(
                api_storage.service_name,
                api_storage.storage_service_properties.description,
                api_storage.storage_service_properties.label,
                None,
                api_storage.storage_service_properties.location,
                None,
                None, 'Standard_LRS')
            self.mox.ReplayAll()

            ret = api.azure_api.storage_account_create(
                self.request,
                api_storage.service_name,
                api_storage.storage_service_properties.description,
                api_storage.storage_service_properties.label,
                location=api_storage.storage_service_properties.location,
                account_type='Standard_LRS')
            # Request Accept 202
            self.assertIsNone(ret)

    def test_role_size_list(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_rolesizes = self.azure_rolesizes.list()
            azureclient = self.stub_azureclient()
            azureclient.list_role_sizes().AndReturn(api_rolesizes)
            self.mox.ReplayAll()

            rolesizes = api.azure_api.role_size_list(self.request)
            self.assertEqual(len(rolesizes), 2)

    def test_deployment_get_by_name(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            azureclient = self.stub_azureclient()
            azureclient.get_deployment_by_name(
                api_cloudservice.service_name,
                api_deployment.name).AndReturn(api_deployment)
            self.mox.ReplayAll()

            deployment = api.azure_api.deployment_get_by_name(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name)
            self.assertIsInstance(deployment, smng.Deployment)

    def test_deployment_create(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            azureclient = self.stub_azureclient()
            azureclient.create_deployment(
                service_name=api_cloudservice.service_name,
                deployment_slot=api_deployment.deployment_slot,
                name=api_deployment.name,
                package_url=api_deployment.url,
                label=api_deployment.label,
                configuration=api_deployment.configuration,
                start_deployment=False,
                treat_warnings_as_error=False,
                extended_properties=None)
            self.mox.ReplayAll()

            ret = api.azure_api.deployment_create(
                self.request,
                service_name=api_cloudservice.service_name,
                deployment_slot=api_deployment.deployment_slot,
                name=api_deployment.name,
                package_url=api_deployment.url,
                label=api_deployment.label,
                configuration=api_deployment.configuration,
                start_deployment=False,
                treat_warnings_as_error=False,
                extended_properties=None)
            # Request Accept 202
            self.assertIsNone(ret)

    def _get_operation(self, azureclient, result):
        operation = self.azure_operation_status.first()
        azureclient.get_operation_status(
            result.request_id).AndReturn(operation)

    def test_deployment_delete(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.delete_deployment(
                api_cloudservice.service_name,
                api_deployment.name).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.deployment_delete(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name)

            self.assertTrue(ret)

    def test_list_os_images(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_os_images = self.azure_os_images.list()
            azureclient = self.stub_azureclient()
            azureclient.list_os_images().AndReturn(api_os_images)
            self.mox.ReplayAll()

            os_images = api.azure_api.list_os_images(self.request)
            self.assertEqual(len(os_images), 2)
            for i in os_images:
                self.assertIsInstance(i, smng.OSImage)

    def test_virtual_machine_get(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            azureclient = self.stub_azureclient()
            azureclient.get_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(api_role)
            self.mox.ReplayAll()

            role = api.azure_api.virtual_machine_get(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name)
            self.assertIsInstance(role, smng.Role)

    def _virtual_machine_create_base(self):
        api_cloudservice = self.azure_cloud_services.first()
        api_deployment = self.azure_deployments.first()
        api_role = self.azure_roles.first()
        result = self.azure_async_results.first()
        azureclient = self.stub_azureclient()
        azureclient.create_hosted_service(
            service_name=api_cloudservice.service_name,
            label=api_cloudservice.service_name,
            location=api_cloudservice.hosted_service_properties.location)
        azureclient.create_virtual_machine_deployment(
            service_name=api_cloudservice.service_name,
            deployment_name=api_deployment.name,
            deployment_slot=api_deployment.deployment_slot,
            label=api_deployment.label,
            role_name=api_role.role_name,
            system_config=IgnoreArg(),
            os_virtual_hard_disk=IgnoreArg(),
            network_config=IgnoreArg(),
            role_size=api_role.role_size).AndReturn(result)
        self._get_operation(azureclient, result)
        self.mox.ReplayAll()

    def test_virtual_machine_create_new_cloudservce_linux(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            self._virtual_machine_create_base()
            ret = api.azure_api.virtual_machine_create(
                self.request,
                api_cloudservice.service_name,
                True,
                api_cloudservice.hosted_service_properties.location,
                api_deployment.name,
                api_deployment.label,
                True,
                api_role.role_name,
                api_role.os_virtual_hard_disk.source_image_name,
                'windows_image_id',
                'username',
                'password',
                deployment_slot='Production',
                network_config=None,
                availability_set_name=None,
                data_virtual_hard_disks=None,
                role_size=api_role.role_size,
                role_type='PersistentVMRole',
                virtual_network_name=None,
                resource_extension_references=None,
                provision_guest_agent=None,
                vm_image_name=None,
                media_location=None,
                dns_servers=None,
                reserved_ip_name=None)

            self.assertTrue(ret)

    def test_virtual_machine_create_add_role_to_cloudservice_deployment(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = \
                self.azure_cloud_services_with_deployment.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.list()[1]
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                service_name=api_cloudservice.service_name,
                embed_detail=True).AndReturn(api_cloudservice)
            azureclient.add_role(
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name,
                system_config=IgnoreArg(),
                os_virtual_hard_disk=IgnoreArg(),
                network_config=IgnoreArg(),
                role_size=api_role.role_size).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_create(
                self.request,
                api_cloudservice.service_name,
                False,
                api_cloudservice.hosted_service_properties.location,
                api_deployment.name,
                api_deployment.label,
                True,
                api_role.role_name,
                api_role.os_virtual_hard_disk.source_image_name,
                'windows_image_id',
                'username',
                'password',
                deployment_slot='Production',
                network_config=None,
                availability_set_name=None,
                data_virtual_hard_disks=None,
                role_size=api_role.role_size,
                role_type='PersistentVMRole',
                virtual_network_name=None,
                resource_extension_references=None,
                provision_guest_agent=None,
                vm_image_name=None,
                media_location=None,
                dns_servers=None,
                reserved_ip_name=None)

            self.assertTrue(ret)

    def test_virtual_machine_create_add_role_to_cloudservice_no_deployment(
        self
    ):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                service_name=api_cloudservice.service_name,
                embed_detail=True).AndReturn(api_cloudservice)
            azureclient.create_virtual_machine_deployment(
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                deployment_slot=api_deployment.deployment_slot,
                label=api_deployment.label,
                role_name=api_role.role_name,
                system_config=IgnoreArg(),
                os_virtual_hard_disk=IgnoreArg(),
                network_config=IgnoreArg(),
                role_size=api_role.role_size).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_create(
                self.request,
                api_cloudservice.service_name,
                False,
                api_cloudservice.hosted_service_properties.location,
                api_deployment.name,
                api_deployment.label,
                True,
                api_role.role_name,
                api_role.os_virtual_hard_disk.source_image_name,
                'windows_image_id',
                'username',
                'password',
                deployment_slot='Production',
                network_config=None,
                availability_set_name=None,
                data_virtual_hard_disks=None,
                role_size=api_role.role_size,
                role_type='PersistentVMRole',
                virtual_network_name=None,
                resource_extension_references=None,
                provision_guest_agent=None,
                vm_image_name=None,
                media_location=None,
                dns_servers=None,
                reserved_ip_name=None)

            self.assertTrue(ret)

    def test_virtual_machine_delete(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.delete_role(
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_delete(
                self.request,
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name)

            self.assertTrue(ret)

    def test_virtual_machine_shutdown(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.shutdown_role(
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name,
                post_shutdown_action='StoppedDeallocated').AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_shutdown(
                self.request,
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name)

            self.assertTrue(ret)

    def test_virtual_machine_restart(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.restart_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_restart(
                self.request,
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name)

            self.assertTrue(ret)

    def test_virtual_machine_start(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.start_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_start(
                self.request,
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name)

            self.assertTrue(ret)

    def test_virtual_machine_resize(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            new_size = self.azure_rolesizes.list()[1]
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                service_name=api_cloudservice.service_name,
                embed_detail=True).AndReturn(api_cloudservice)
            azureclient.get_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(api_role)
            azureclient.update_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                role_size=new_size.name,
                network_config=IgnoreArg()).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_resize(
                self.request,
                service_name=api_cloudservice.service_name,
                deployment_name=api_deployment.name,
                role_name=api_role.role_name,
                role_size=new_size.name)

            self.assertTrue(ret)

    def test_virtual_machine_add_endpoint(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = \
                self.azure_cloud_services_with_deployment.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                service_name=api_cloudservice.service_name,
                embed_detail=True).AndReturn(api_cloudservice)
            azureclient.get_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(api_role)
            azureclient.update_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                network_config=IgnoreArg()).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_add_endpoint(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                'http',
                'TCP',
                8080)

            self.assertTrue(ret)

    def test_virtual_machine_remove_endpoint(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = \
                self.azure_cloud_services_with_deployment.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                service_name=api_cloudservice.service_name,
                embed_detail=True).AndReturn(api_cloudservice)
            azureclient.get_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(api_role)
            azureclient.update_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                network_config=IgnoreArg()).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.virtual_machine_remove_endpoint(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                'ssh')

            self.assertTrue(ret)

    def test_disk_list(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_disks = self.azure_disks.list()
            azureclient = self.stub_azureclient()
            azureclient.list_disks().AndReturn(api_disks)
            self.mox.ReplayAll()

            disks = api.azure_api.disk_list(self.request)
            self.assertEqual(len(disks), 2)
            for d in disks:
                self.assertIsInstance(d, smng.Disk)

    def test_disk_get(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_disk = self.azure_disks.first()
            azureclient = self.stub_azureclient()
            azureclient.get_disk(api_disk.name).AndReturn(api_disk)
            self.mox.ReplayAll()

            disk = api.azure_api.disk_get(self.request, api_disk.name)
            self.assertIsInstance(disk, smng.Disk)

    def test_disk_delete(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_disk = self.azure_disks.first()
            azureclient = self.stub_azureclient()
            azureclient.delete_disk(api_disk.name,
                                    False)
            self.mox.ReplayAll()

            ret = api.azure_api.disk_delete(self.request, api_disk.name)
            # Request Accept 202
            self.assertIsNone(ret)

    def test_data_disk_get(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_disk = self.azure_data_disks.first()
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            azureclient = self.stub_azureclient()
            azureclient.get_data_disk(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                0).AndReturn(api_disk)
            self.mox.ReplayAll()

            disk = api.azure_api.data_disk_get(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                0)
            self.assertIsInstance(disk, smng.Disk)

    def test_data_disk_attach(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.list()[1]
            api_deployment = self.azure_deployments.list()[1]
            api_role = self.azure_roles.list()[1]
            api_rolesizes = self.azure_rolesizes.list()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.get_hosted_service_properties(
                api_cloudservice.service_name).AndReturn(api_cloudservice)
            azureclient.get_role(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name).AndReturn(api_role)
            azureclient.list_role_sizes().AndReturn(api_rolesizes)
            azureclient.add_data_disk(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                0,
                None,
                IgnoreArg(),
                None,
                disk_name=None,
                logical_disk_size_in_gb=1,
                source_media_link=None).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.data_disk_attach(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                logical_disk_size_in_gb=1)

            self.assertTrue(ret)

    def test_data_disk_deattach(self):
        with patch('azure.servicemanagement.servicemanagementservice.'
                   'ServiceManagementService.timeout',
                   new_callable=PropertyMock) as mock_timeout:
            mock_timeout.return_value = 65
            api_cloudservice = self.azure_cloud_services.first()
            api_deployment = self.azure_deployments.first()
            api_role = self.azure_roles.first()
            result = self.azure_async_results.first()
            azureclient = self.stub_azureclient()
            azureclient.delete_data_disk(
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                0,
                False).AndReturn(result)
            self._get_operation(azureclient, result)
            self.mox.ReplayAll()

            ret = api.azure_api.data_disk_deattach(
                self.request,
                api_cloudservice.service_name,
                api_deployment.name,
                api_role.role_name,
                0,
                False)

            self.assertTrue(ret)
