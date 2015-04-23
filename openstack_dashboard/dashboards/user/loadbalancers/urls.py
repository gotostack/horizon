# Copyright 2015 Letv Cloud Computing
# All Rights Reserved.
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

from openstack_dashboard.dashboards.user.loadbalancers import views


LOADBALANCER_URL = r'^(?P<loadbalancer_id>[^/]+)/%s'


urlpatterns = patterns(
    'openstack_dashboard.dashboards.user.loadbalancers.views',
    url(r'^$', views.IndexView.as_view(), name='index'),

    url(r'^addloadbalancer$',
        views.AddLoadbalancerView.as_view(), name='addloadbalancer'),
    url(r'^updateloadbalancer/(?P<loadbalancer_id>[^/]+)/$',
        views.UpdateLoadbalancerView.as_view(), name='updateloadbalancer'),
    url(LOADBALANCER_URL % '$',
        views.LoadbalancerDetailView.as_view(),
        name='detail'),

    url(r'^addlistener$',
        views.AddListenerView.as_view(), name='addlistener'),
    url(r'^updatelistener/(?P<listener_id>[^/]+)/$',
        views.UpdateListenerView.as_view(), name='updatelistener'),
    url(r'^listener/(?P<listener_id>[^/]+)/$',
        views.ListenerDetailsView.as_view(), name='listenerdetails'),

    url(r'^addpool$',
        views.AddPoolView.as_view(), name='addpool'),
    url(r'^updatepool/(?P<pool_id>[^/]+)/$',
        views.UpdatePoolView.as_view(), name='updatepool'),
    url(r'^pool/(?P<pool_id>[^/]+)/$',
        views.PoolDetailsView.as_view(), name='pooldetails'),

    url(r'^addmember/(?P<pool_id>[^/]+)/$',
        views.AddMemberView.as_view(), name='addmember'),
    url(r'^updatemember/(?P<pool_id>[^/]+)/(?P<member_id>[^/]+)/$',
        views.UpdateMemberView.as_view(), name='updatemember'),
    #url(r'^member/(?P<member_id>[^/]+)/$',
    #    views.MemberDetailsView.as_view(), name='memberdetails')
    )
