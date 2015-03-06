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

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.lecloud.instances import views


INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'
AZURE_MOD = r'^(?P<cloud_service_name>[^/]+)_(?P<deployment_name>[^/]+)' \
    '_(?P<instance_name>[^/]+)/%s$'
VIEW_MOD = 'openstack_dashboard.dashboards.lecloud.instances.views'


urlpatterns = patterns(
    VIEW_MOD,
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^launch$', views.LaunchInstanceView.as_view(), name='launch'),
    url(AZURE_MOD % 'update', views.UpdateView.as_view(), name='update'),
    url(AZURE_MOD % 'detail', views.DetailView.as_view(), name='detail'),
    url(AZURE_MOD % 'resize', views.ResizeView.as_view(), name='resize'),
    url(AZURE_MOD % 'addendpoint',
        views.AddEndpointView.as_view(), name='addendpoint'),
    url(AZURE_MOD % 'removeendpoint',
        views.RemoveEndpointView.as_view(), name='removeendpoint'),
    url(AZURE_MOD % 'attach',
        views.AttachDataDiskView.as_view(), name='attach'),
    url(AZURE_MOD % 'deattach',
        views.DeattachDataDiskView.as_view(), name='deattach'),
)
