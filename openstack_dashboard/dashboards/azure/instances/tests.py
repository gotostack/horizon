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

from django.core.urlresolvers import reverse
from django import http
from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.azure.instances import workflows
from openstack_dashboard.test import helpers

INDEX_URL = reverse('horizon:azure:instances:index')


class InstanceTests(helpers.TestCase):
    @helpers.create_stubs({
        api.azure_api: (
            'cloud_service_list',
            'role_size_list',
            'cloud_service_detail',
        ),
    })
    def test_index(self):
        cloud_services = self.azure_cloud_services.list()
        role_sizes = self.azure_rolesizes.list()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        detail_2 = self.azure_cloud_services_with_deployment.list()[1]

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_1.service_name,
            embed_detail=True).AndReturn(detail_1)
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_2.service_name,
            embed_detail=True).AndReturn(detail_2)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'azure/instances/index.html')

        self.assertIn('instances_table', res.context)
        instances_table = res.context['instances_table']
        instances_row = instances_table.data
        # Instances
        self.assertEqual(len(instances_row), 2)

        # Table actions
        self.assertEqual(len(instances_table.get_table_actions()), 5)

        # Row actions
        row_actions = instances_table.get_row_actions(instances_row[0])
        self.assertEqual(len(row_actions), 9)
        row_actions = instances_table.get_row_actions(instances_row[1])
        self.assertEqual(len(row_actions), 9)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',)})
    def test_index_cloud_service_list_exception(self):
        role_sizes = self.azure_rolesizes.list()
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)
        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'azure/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',)})
    def test_index_role_size_list_exception(self):
        cloud_services = self.azure_cloud_services.list()
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'azure/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail')})
    def test_index_cloud_service_detail_exception(self):
        cloud_services = self.azure_cloud_services.list()
        role_sizes = self.azure_rolesizes.list()

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            IgnoreArg(),
            embed_detail=True).MultipleTimes().AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'azure/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
        self.assertMessageCount(res, error=1)

    def _terminate_instance_base(self):
        cloud_services = self.azure_cloud_services.list()
        role_sizes = self.azure_rolesizes.list()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        detail_2 = self.azure_cloud_services_with_deployment.list()[1]

        # Add a role to the deployment in order to make sure
        # this instance is not the last role of the deployment
        role = self.azure_roles.list()[1]
        detail_1.deployments[0].role_list.roles.append(role)

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_1.service_name,
            embed_detail=True).AndReturn(detail_1)
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_2.service_name,
            embed_detail=True).AndReturn(detail_2)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_1.service_name,
            True).AndReturn(detail_1)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'virtual_machine_delete')})
    def test_terminate_instance(self):
        server = self.azure_role_instances.first()
        detail_1 = self.azure_cloud_services_with_deployment.first()

        self._terminate_instance_base()
        api.azure_api.virtual_machine_delete(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name)
        self.mox.ReplayAll()

        formData = {
            'action': 'instances__terminate__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'virtual_machine_delete')})
    def test_terminate_instance_exception(self):
        server = self.azure_role_instances.first()
        detail_1 = self.azure_cloud_services_with_deployment.first()

        self._terminate_instance_base()
        api.azure_api.virtual_machine_delete(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__terminate__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def _get_instances_actions_base(self):
        cloud_services = self.azure_cloud_services.list()
        role_sizes = self.azure_rolesizes.list()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        detail_2 = self.azure_cloud_services_with_deployment.list()[1]

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_1.service_name,
            embed_detail=True).AndReturn(detail_1)
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_2.service_name,
            embed_detail=True).AndReturn(detail_2)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'deployment_delete')})
    def test_terminate_instance_last_role(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_1.service_name,
            True).AndReturn(detail_1)
        api.azure_api.deployment_delete(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name)
        self.mox.ReplayAll()

        formData = {
            'action': 'instances__terminate__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'deployment_delete')})
    def test_terminate_instance_last_role_exception(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            detail_1.service_name,
            True).AndReturn(detail_1)
        api.azure_api.deployment_delete(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        formData = {
            'action': 'instances__terminate__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list')})
    def test_launch_instance_get(self):
        role_sizes = self.azure_rolesizes.list()
        azure_os_images = self.azure_os_images.list()
        cloud_services = self.azure_cloud_services.list()
        locations = self.azure_locations.list()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.list_os_images(
            IsA(http.HttpRequest)).AndReturn(azure_os_images)
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')
        res = self.client.get(url)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(res.context['workflow'].name,
                         workflows.LaunchInstance.name)

        self.assertQuerysetEqual(
            workflow.steps,
            ['<SetInstanceDetails: setinstancedetailsaction>',
             '<SetAzureOSImageStep: setazureosimageaction>',
             '<SetAccessControls: setaccesscontrolsaction>'])

        self.assertContains(
            res,
            '<option value="flavor_basic">Basic</option>')
        self.assertContains(
            res,
            '<option value="flavor_standard">Standard</option>')
        self.assertContains(
            res,
            '<option value="Basic_A0">Basic_A0 '
            '(1 cores, 768 MB)</option>')
        self.assertContains(
            res,
            '<option value="A5">A5 (2 cores, 14336 MB)</option>')

        self.assertContains(res, 'Boot from linux image')
        self.assertContains(res, 'Ubuntu Server 14.10')
        self.assertContains(res, 'Boot from windows image')
        self.assertContains(
            res, 'Windows Server Essentials '
                 'Experience on Windows Server 2012 R2 (en-us)')

        self.assertContains(res, 'Add a new cloud service')
        self.assertContains(
            res, '<option value="China East">China East</option>')
        self.assertContains(
            res, '<option value="China North">China North</option>')

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list')})
    def test_launch_instance_get_rolesizes_exception(self):
        azure_os_images = self.azure_os_images.list()
        cloud_services = self.azure_cloud_services.list()
        locations = self.azure_locations.list()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)
        api.azure_api.list_os_images(
            IsA(http.HttpRequest)).AndReturn(azure_os_images)
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')
        res = self.client.get(url)

        self.assertMessageCount(res, error=1)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list')})
    def test_launch_instance_list_os_images_exception(self):
        role_sizes = self.azure_rolesizes.list()
        cloud_services = self.azure_cloud_services.list()
        locations = self.azure_locations.list()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.list_os_images(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')
        res = self.client.get(url)

        self.assertMessageCount(res, error=1)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list')})
    def test_launch_instance_cloud_service_list_exception(self):
        role_sizes = self.azure_rolesizes.list()
        azure_os_images = self.azure_os_images.list()
        locations = self.azure_locations.list()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.list_os_images(
            IsA(http.HttpRequest)).AndReturn(azure_os_images)
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)
        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')
        res = self.client.get(url)

        self.assertMessageCount(res, error=1)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list')})
    def test_launch_instance_azure_locations_exception(self):
        role_sizes = self.azure_rolesizes.list()
        azure_os_images = self.azure_os_images.list()
        cloud_services = self.azure_cloud_services.list()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.list_os_images(
            IsA(http.HttpRequest)).AndReturn(azure_os_images)
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')
        res = self.client.get(url)

        self.assertMessageCount(res, error=1)

    def _launch_instance_post_base(self):
        role_sizes = self.azure_rolesizes.list()
        azure_os_images = self.azure_os_images.list()
        cloud_services = self.azure_cloud_services.list()
        locations = self.azure_locations.list()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.list_os_images(
            IsA(http.HttpRequest)).AndReturn(azure_os_images)
        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)
        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list',
                                           'virtual_machine_create')})
    def test_launch_instance_post(self):
        role_size = self.azure_rolesizes.first()
        image = self.azure_os_images.first()

        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()

        self._launch_instance_post_base()
        api.azure_api.virtual_machine_create(
            IsA(http.HttpRequest),
            service_name=cloud_service.service_name,
            location=cloud_service.hosted_service_properties.location,
            create_new_cloudservice=True,
            deployment_name=cloud_service.service_name,
            label=server.instance_name,
            enable_port=True,
            role_name=server.instance_name,
            image_name=image.name,
            image_type='linux_image_id',
            admin_username='username',
            user_password='password',
            role_size=role_size.name)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')

        form_data = {
            'name': server.instance_name,
            'role_size_type': 'flavor_basic',
            'flavor_basic': role_size.name,
            'azure_source_type': 'linux_image_id',
            'linux_image_id': image.name,
            'access_user_name': 'username',
            'admin_pass': 'password',
            'confirm_admin_pass': 'password',
            'enable_port': True,
            'cloud_services': 'new_cloudservice',
            'cloud_service_name': cloud_service.service_name,
            'location': cloud_service.hosted_service_properties.location}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'list_os_images',
                                           'cloud_service_list',
                                           'location_list',
                                           'virtual_machine_create')})
    def test_launch_instance_post_exception(self):
        role_size = self.azure_rolesizes.first()
        image = self.azure_os_images.first()

        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()

        self._launch_instance_post_base()
        api.azure_api.virtual_machine_create(
            IsA(http.HttpRequest),
            service_name=cloud_service.service_name,
            location=cloud_service.hosted_service_properties.location,
            create_new_cloudservice=True,
            deployment_name=cloud_service.service_name,
            label=server.instance_name,
            enable_port=True,
            role_name=server.instance_name,
            image_name=image.name,
            image_type='linux_image_id',
            admin_username='username',
            user_password='password',
            role_size=role_size.name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:launch')

        form_data = {
            'name': server.instance_name,
            'role_size_type': 'flavor_basic',
            'flavor_basic': role_size.name,
            'azure_source_type': 'linux_image_id',
            'linux_image_id': image.name,
            'access_user_name': 'username',
            'admin_pass': 'password',
            'confirm_admin_pass': 'password',
            'enable_port': True,
            'cloud_services': 'new_cloudservice',
            'cloud_service_name': cloud_service.service_name,
            'location': cloud_service.hosted_service_properties.location}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'virtual_machine_shutdown')})
    def test_stop_instance(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()

        api.azure_api.virtual_machine_shutdown(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__stop__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'virtual_machine_shutdown')})
    def test_stop_instance_exception(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()
        api.azure_api.virtual_machine_shutdown(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__stop__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'virtual_machine_restart')})
    def test_restart_instance(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()

        api.azure_api.virtual_machine_restart(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__restart__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'virtual_machine_restart')})
    def test_restart_instance_exception(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()
        api.azure_api.virtual_machine_restart(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__restart__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get')})
    def test_resize_instance_get(self):
        role_sizes = self.azure_rolesizes.list()
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        role = self.azure_roles.first()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:resize',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @helpers.create_stubs({api.azure_api: ('virtual_machine_get',)})
    def test_resize_instance_virtual_machine_get_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()

        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:resize',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get')})
    def test_resize_instance_role_size_list_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        role = self.azure_roles.first()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.azure)
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:resize',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def _resize_post_base(self):
        role_sizes = self.azure_rolesizes.list()
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        role = self.azure_roles.first()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get',
                                           'virtual_machine_resize')})
    def test_resize_post(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        old_size = self.azure_rolesizes.first()
        new_size = self.azure_rolesizes.list()[1]
        self._resize_post_base()

        api.azure_api.virtual_machine_resize(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            new_size.name)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:resize',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'old_flavor_id': old_size.name,
            'old_flavor_name': old_size.name,
            'role_size_type': 'flavor_standard',
            'flavor_standard': new_size.name}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get',
                                           'virtual_machine_resize')})
    def test_resize_post_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        old_size = self.azure_rolesizes.first()
        new_size = self.azure_rolesizes.list()[1]
        self._resize_post_base()

        api.azure_api.virtual_machine_resize(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            new_size.name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:resize',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'old_flavor_id': old_size.name,
            'old_flavor_name': old_size.name,
            'role_size_type': 'flavor_standard',
            'flavor_standard': new_size.name}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get')})
    def test_update_instance_get(self):
        role_sizes = self.azure_rolesizes.list()
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        role = self.azure_roles.first()

        api.azure_api.role_size_list(
            IsA(http.HttpRequest)).AndReturn(role_sizes)
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:update',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get',
                                           'virtual_machine_update')})
    def test_update_post(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        self._resize_post_base()
        aset_name = 'availablility-set'

        api.azure_api.virtual_machine_update(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            availability_set_name=aset_name)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:update',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'availability_set_name': aset_name}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('role_size_list',
                                           'virtual_machine_get',
                                           'virtual_machine_update')})
    def test_update_post_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        self._resize_post_base()
        aset_name = 'availablility-set'

        api.azure_api.virtual_machine_update(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            availability_set_name=aset_name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:update',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'availability_set_name': aset_name}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_add_endpoint_instance_get(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        url = reverse('horizon:azure:instances:addendpoint',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'azure/instances/add_endpoint.html')

    @helpers.create_stubs({api.azure_api: ('virtual_machine_add_endpoint',)})
    def test_add_endpoint_instance_post(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        endpoint = self.azure_endpoints.list()[1]
        api.azure_api.virtual_machine_add_endpoint(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            endpoint.name,
            endpoint.protocol,
            endpoint.local_port,
            endpoint.public_port)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:addendpoint',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'cloud_service_name': cloud_service.service_name,
            'deployment_name': deployment.name,
            'instance_name': server.role_name,
            'endpoint_name': endpoint.name,
            'protocol': endpoint.protocol,
            'port': endpoint.local_port,
            'public_port': endpoint.public_port}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('virtual_machine_add_endpoint',)})
    def test_add_endpoint_instance_post_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        endpoint = self.azure_endpoints.list()[1]
        api.azure_api.virtual_machine_add_endpoint(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            endpoint.name,
            endpoint.protocol,
            endpoint.local_port,
            endpoint.public_port).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:addendpoint',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'cloud_service_name': cloud_service.service_name,
            'deployment_name': deployment.name,
            'instance_name': server.role_name,
            'endpoint_name': endpoint.name,
            'protocol': endpoint.protocol,
            'port': endpoint.local_port,
            'public_port': endpoint.public_port}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('virtual_machine_get',)})
    def test_remove_endpoint_instance_get(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        role = self.azure_roles.first()
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)
        self.mox.ReplayAll()
        url = reverse('horizon:azure:instances:removeendpoint',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'azure/instances/remove_endpoint.html')

    @helpers.create_stubs({
        api.azure_api: ('virtual_machine_get',
                        'virtual_machine_remove_endpoint',)})
    def test_remove_endpoint_instance_post(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        endpoint = self.azure_endpoints.first()
        api.azure_api.virtual_machine_remove_endpoint(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            endpoint.name)
        role = self.azure_roles.first()
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:removeendpoint',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'cloud_service_name': cloud_service.service_name,
            'deployment_name': deployment.name,
            'instance_name': server.role_name,
            'endpoints': endpoint.name}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('virtual_machine_get',
                        'virtual_machine_remove_endpoint',)})
    def test_remove_endpoint_instance_post_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        endpoint = self.azure_endpoints.first()
        api.azure_api.virtual_machine_remove_endpoint(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name,
            endpoint.name).AndRaise(self.exceptions.azure)
        role = self.azure_roles.first()
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:removeendpoint',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'cloud_service_name': cloud_service.service_name,
            'deployment_name': deployment.name,
            'instance_name': server.role_name,
            'endpoints': endpoint.name}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_attatch_datadisk_instance_get(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        url = reverse('horizon:azure:instances:attach',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'azure/instances/attach_datadisk.html')

    @helpers.create_stubs({api.azure_api: ('data_disk_attach',)})
    def test_attatch_datadisk_instance_post(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        data_disk = self.azure_data_disks.first()
        api.azure_api.data_disk_attach(
            IsA(http.HttpRequest),
            service_name=cloud_service.service_name,
            deployment_name=deployment.name,
            role_name=server.role_name,
            logical_disk_size_in_gb=data_disk.logical_disk_size_in_gb
        ).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:attach',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'cloud_service_name': cloud_service.service_name,
            'deployment_name': deployment.name,
            'instance_name': server.role_name,
            'disk_name': data_disk.name,
            'size': data_disk.logical_disk_size_in_gb}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('data_disk_attach',)})
    def test_attatch_datadisk_instance_post_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        data_disk = self.azure_data_disks.first()
        api.azure_api.data_disk_attach(
            IsA(http.HttpRequest),
            service_name=cloud_service.service_name,
            deployment_name=deployment.name,
            role_name=server.role_name,
            logical_disk_size_in_gb=data_disk.logical_disk_size_in_gb)
        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:attach',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        form_data = {
            'cloud_service_name': cloud_service.service_name,
            'deployment_name': deployment.name,
            'instance_name': server.role_name,
            'disk_name': data_disk.name,
            'size': data_disk.logical_disk_size_in_gb}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'data_disk_deattach')})
    def test_deattach_datadisk_instance(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()

        api.azure_api.data_disk_deattach(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__de-attach__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_list',
                                           'role_size_list',
                                           'cloud_service_detail',
                                           'data_disk_deattach')})
    def test_deattach_datadisk_instance_exception(self):
        self._get_instances_actions_base()
        detail_1 = self.azure_cloud_services_with_deployment.first()
        server = self.azure_role_instances.first()

        api.azure_api.data_disk_deattach(
            IsA(http.HttpRequest),
            detail_1.service_name,
            detail_1.service_name,
            server.instance_name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        formData = {
            'action': 'instances__de-attach__%s==%s' % (
                detail_1.service_name, server.instance_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('virtual_machine_get',)})
    def test_instance_detail_get(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        role = self.azure_roles.first()
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndReturn(role)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:detail',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'azure/instances/detail.html')
        self.assertContains(
            res, '<dd>testvm01linux</dd>')
        self.assertContains(
            res,
            '<dd>Protocol: tcp | Name: SSH |'
            ' Public Port: 10022 | Local Port: 22</dd>')
        self.assertContains(
            res, '<dt>Attached To</dt>')
        self.assertContains(
            res, '<dd>Volume Name: letvcloudservicetest01-testvm01linux'
                 '-0-201502120658120720 | Size: 1 GB</dd>')

    @helpers.create_stubs({api.azure_api: ('virtual_machine_get',)})
    def test_instance_detail_get_exception(self):
        server = self.azure_role_instances.first()
        cloud_service = self.azure_cloud_services.first()
        deployment = self.azure_deployments.first()
        api.azure_api.virtual_machine_get(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            deployment.name,
            server.role_name).AndRaise(self.exceptions.azure)

        self.mox.ReplayAll()

        url = reverse('horizon:azure:instances:detail',
                      args=[cloud_service.service_name,
                            deployment.name,
                            server.role_name])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)


class InstanceAjaxTests(helpers.TestCase):
    pass
