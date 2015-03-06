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

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers

INDEX_URL = reverse('horizon:lecloud:cloudservices:index')


class CloudServicesViewTests(helpers.TestCase):
    @helpers.create_stubs({
        api.azure_api: ('cloud_service_list',
                        'cloud_service_detail')})
    def test_index(self):
        cloud_services = self.azure_cloud_services.list()
        cs_with_deployment = self.azure_cloud_services_with_deployment.first()
        cs_no_deployment = self.azure_cloud_services.list()[1]

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cs_with_deployment.service_name,
            True).MultipleTimes().AndReturn(cs_with_deployment)
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cs_no_deployment.service_name,
            True).MultipleTimes().AndReturn(cs_no_deployment)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'lecloud/cloudservices/index.html')

        self.assertIn('cloud_services_table', res.context)
        cloudservices_table = res.context['cloud_services_table']
        cloudservices_row = cloudservices_table.data
        # Cloud Services
        self.assertEqual(len(cloudservices_row), 2)

        # Table actions
        self.assertEqual(len(cloudservices_table.get_table_actions()), 3)

        # Row actions
        row_actions = cloudservices_table.get_row_actions(cloudservices_row[0])
        self.assertEqual(len(row_actions), 1)
        row_actions = cloudservices_table.get_row_actions(cloudservices_row[1])
        self.assertEqual(len(row_actions), 1)

    @helpers.create_stubs({
        api.azure_api: ('location_list',)})
    def test_create_cloud_service_get(self):
        locations = self.azure_locations.list()

        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)

        self.mox.ReplayAll()

        url = reverse('horizon:lecloud:cloudservices:create')
        res = self.client.get(url)

        self.assertTemplateUsed(
            res,
            'lecloud/cloudservices/create_cloudservice.html')
        self.assertContains(
            res, '<option value="China East">China East</option>')
        self.assertContains(
            res, '<option value="China North">China North</option>')

    @helpers.create_stubs({
        api.azure_api: ('location_list',
                        'cloud_service_create')})
    def test_create_cloud_service_post(self):
        locations = self.azure_locations.list()
        location = self.azure_locations.first()
        cloud_service = self.azure_cloud_services.first()

        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)
        api.azure_api.cloud_service_create(
            IsA(http.HttpRequest),
            service_name=cloud_service.service_name,
            label=cloud_service.service_name,
            description=cloud_service.hosted_service_properties.description,
            location=location.name)
        self.mox.ReplayAll()

        url = reverse('horizon:lecloud:cloudservices:create')

        form_data = {
            'service_name': cloud_service.service_name,
            'location': location.name,
            'description':
                cloud_service.hosted_service_properties.description}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('location_list',
                        'cloud_service_create')})
    def test_create_cloud_service_post_exception(self):
        locations = self.azure_locations.list()
        location = self.azure_locations.first()
        cloud_service = self.azure_cloud_services.first()

        api.azure_api.location_list(
            IsA(http.HttpRequest)).AndReturn(locations)
        api.azure_api.cloud_service_create(
            IsA(http.HttpRequest),
            service_name=cloud_service.service_name,
            label=cloud_service.service_name,
            description=cloud_service.hosted_service_properties.description,
            location=location.name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        url = reverse('horizon:lecloud:cloudservices:create')

        form_data = {
            'service_name': cloud_service.service_name,
            'location': location.name,
            'description':
                cloud_service.hosted_service_properties.description}
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('cloud_service_list',
                        'cloud_service_detail',
                        'deployment_delete')})
    def test_delete_deployment(self):
        cloud_services = self.azure_cloud_services.list()
        cs_with_deployment = self.azure_cloud_services_with_deployment.first()
        deployment = self.azure_deployments.first()

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cs_with_deployment.service_name,
            True).MultipleTimes().AndReturn(cs_with_deployment)

        api.azure_api.deployment_delete(
            IsA(http.HttpRequest),
            cs_with_deployment.service_name,
            deployment.name)
        self.mox.ReplayAll()

        formData = {
            'action': ('cloud_services__deletedeployment__%s' %
                       cs_with_deployment.service_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('cloud_service_list',
                        'cloud_service_detail',
                        'deployment_delete')})
    def test_delete_deployment_exception(self):
        cloud_services = self.azure_cloud_services.list()
        cs_with_deployment = self.azure_cloud_services_with_deployment.first()
        deployment = self.azure_deployments.first()

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cs_with_deployment.service_name,
            True).MultipleTimes().AndReturn(cs_with_deployment)

        api.azure_api.deployment_delete(
            IsA(http.HttpRequest),
            cs_with_deployment.service_name,
            deployment.name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        formData = {
            'action': ('cloud_services__deletedeployment__%s' %
                       cs_with_deployment.service_name)}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('cloud_service_list',
                        'cloud_service_detail',
                        'cloud_service_delete')})
    def test_delete_cloud_service(self):
        cloud_services = self.azure_cloud_services.list()
        cloud_service = self.azure_cloud_services.first()

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            True).MultipleTimes().AndReturn(cloud_service)

        api.azure_api.cloud_service_delete(
            IsA(http.HttpRequest),
            cloud_service.service_name)
        self.mox.ReplayAll()

        formData = {
            'action':
                'cloud_services__delete__%s' % cloud_service.service_name}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.azure_api: ('cloud_service_list',
                        'cloud_service_detail',
                        'cloud_service_delete')})
    def test_delete_cloud_service_exception(self):
        cloud_services = self.azure_cloud_services.list()
        cloud_service = self.azure_cloud_services.first()

        api.azure_api.cloud_service_list(
            IsA(http.HttpRequest)).AndReturn(cloud_services)

        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            True).MultipleTimes().AndReturn(cloud_service)

        api.azure_api.cloud_service_delete(
            IsA(http.HttpRequest),
            cloud_service.service_name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        formData = {
            'action':
                'cloud_services__delete__%s' % cloud_service.service_name}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.azure_api: ('cloud_service_detail',)})
    def test_cloud_service_detail_get(self):
        cloud_service = self.azure_cloud_services_with_deployment.first()
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cloud_service.service_name).AndReturn(cloud_service)
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cloud_service.service_name,
            True).MultipleTimes().AndReturn(cloud_service)

        self.mox.ReplayAll()

        url = reverse('horizon:lecloud:cloudservices:detail',
                      args=[cloud_service.service_name])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'lecloud/cloudservices/detail.html')
        self.assertContains(res, '<dd>letvcloudservicetest01</dd>')
        self.assertContains(res, '2015-02-10T08:18:35Z')
        self.assertContains(res, '<dd>Created</dd>')

    @helpers.create_stubs({api.azure_api: ('cloud_service_detail',)})
    def test_cloud_service_detail_get_exception(self):
        cloud_service = self.azure_cloud_services.first()
        api.azure_api.cloud_service_detail(
            IsA(http.HttpRequest),
            cloud_service.service_name).AndRaise(self.exceptions.azure)
        self.mox.ReplayAll()

        url = reverse('horizon:lecloud:cloudservices:detail',
                      args=[cloud_service.service_name])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
