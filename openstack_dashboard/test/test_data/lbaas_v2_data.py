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

from openstack_dashboard.api import lbaas_v2
from openstack_dashboard.test.test_data import utils


def data(TEST):
    # Data returned by openstack_dashboard.api.neutron wrapper.
    TEST.v2_loadbalancers = utils.TestDataContainer()
    TEST.v2_loadbalancer_stats = utils.TestDataContainer()
    TEST.v2_listeners = utils.TestDataContainer()
    TEST.v2_acls = utils.TestDataContainer()
    TEST.v2_pools = utils.TestDataContainer()
    TEST.v2_members = utils.TestDataContainer()
    TEST.v2_healthmonitors = utils.TestDataContainer()

    # Data return by neutronclient.
    TEST.v2_api_loadbalancers = utils.TestDataContainer()
    TEST.v2_api_loadbalancer_stats = utils.TestDataContainer()
    TEST.v2_api_listeners = utils.TestDataContainer()
    TEST.v2_api_acls = utils.TestDataContainer()
    TEST.v2_api_pools = utils.TestDataContainer()
    TEST.v2_api_members = utils.TestDataContainer()
    TEST.v2_api_healthmonitors = utils.TestDataContainer()

    # LBaaS V2.

    # 1st loadbalancer.
    loadbalancer_dict = {
        "description": "dashboard-lb1",
        "admin_state_up": True,
        "tenant_id": "1",
        "provisioning_status": "ACTIVE",
        "agent": "",
        "listeners": [{
            "id": "1efa3b31-9d05-4cc3-ab5c-6a9add115d40"
        }],
        "vip_address": "192.168.0.100",
        "vip_port_id": "063cf7f3-ded1-4297-bc4c-31eae876cc91",
        "provider": "haproxy",
        "vip_subnet_id": "e8abc972-eb0c-41f1-9edd-4bc6e3bcd8c9",
        "id": "183b46dc-57a5-42cb-8f9b-253afce781b2",
        "operating_status": "ONLINE",
        "name": "dashboard-lb1"
    }
    TEST.v2_api_loadbalancers.add(loadbalancer_dict)
    TEST.v2_loadbalancers.add(lbaas_v2.Loadbalancer(loadbalancer_dict))

    # stats for 1st loadbalancer.
    stats_dict = {"bytes_in": 10,
                  "total_connections": 20,
                  "active_connections": 30,
                  "bytes_out": 40}
    TEST.v2_loadbalancer_stats.add(stats_dict)
    TEST.v2_api_loadbalancer_stats.add(lbaas_v2.LoadbalancerStats(stats_dict))

    # 1st listener.
    listener_dict = {
        "protocol_port": 8889,
        "protocol": "TCP",
        "description": "dashboard-ls1",
        "sni_container_ids": [],
        "admin_state_up": True,
        "loadbalancers": [{
            "id": "183b46dc-57a5-42cb-8f9b-253afce781b2"
        }],
        "tenant_id": "1",
        "default_tls_container_id": None,
        "connection_limit": -1,
        "default_pool_id": "56c0bd60-1cd7-478b-a3fa-2c22ae6971d2",
        "id": "1efa3b31-9d05-4cc3-ab5c-6a9add115d40",
        "name": "ls1"
    }
    TEST.v2_api_listeners.add(listener_dict)
    TEST.v2_listeners.add(lbaas_v2.Listener(listener_dict))

    # 1st pool.
    pool_dict = {
        "lb_algorithm": "ROUND_ROBIN",
        "protocol": "TCP",
        "description": "dashboard-pool1",
        "admin_state_up": True,
        "tenant_id": "1",
        "session_persistence": None,
        "healthmonitor_id": "63385c8c-eebf-4019-970a-e0c428cea215",
        "listeners": [{
            "id": "1efa3b31-9d05-4cc3-ab5c-6a9add115d40"
        }],
        "members": [{
            "id": "a0aa3e93-9bf5-4404-941e-984e6bb2c7eb"
        }, {
            "id": "da60a6dd-6630-4290-96c9-20be4433eb1b"
        }],
        "id": "56c0bd60-1cd7-478b-a3fa-2c22ae6971d2",
        "name": "dashboard-pool1"
    }
    TEST.v2_api_pools.add(pool_dict)
    TEST.v2_pools.add(lbaas_v2.Pool(pool_dict))

    # 1st healthmonitor for pool 1st.
    healthmonitor_dict = {
        "admin_state_up": True,
        "tenant_id": "1",
        "delay": 1,
        "expected_codes": "200",
        "max_retries": 1,
        "http_method": "GET",
        "timeout": 1,
        "pools": [{
            "id": "56c0bd60-1cd7-478b-a3fa-2c22ae6971d2"
        }],
        "url_path": "/",
        "type": "PING",
        "id": "63385c8c-eebf-4019-970a-e0c428cea215"
    }
    TEST.v2_api_healthmonitors.add(healthmonitor_dict)
    TEST.v2_healthmonitors.add(lbaas_v2.Healthmonitor(healthmonitor_dict))

    # 1st member for pool 1st.
    member_dict_1 = {
        "weight": 1,
        "admin_state_up": True,
        "subnet_id": "e8abc972-eb0c-41f1-9edd-4bc6e3bcd8c9",
        "tenant_id": "1",
        "address": "8.8.8.8",
        "protocol_port": 22,
        "id": "a0aa3e93-9bf5-4404-941e-984e6bb2c7eb"
    }
    TEST.v2_api_members.add(member_dict_1)
    TEST.v2_members.add(lbaas_v2.Member(member_dict_1))

    # 2nd member for pool 1st.
    member_dict_2 = {
        "weight": 2,
        "admin_state_up": True,
        "subnet_id": "e8abc972-eb0c-41f1-9edd-4bc6e3bcd8c9",
        "tenant_id": "1",
        "address": "9.9.9.9",
        "protocol_port": 22,
        "id": "da60a6dd-6630-4290-96c9-20be4433eb1b"
    }
    TEST.v2_api_members.add(member_dict_2)
    TEST.v2_members.add(lbaas_v2.Member(member_dict_2))

    # 1st acl for listener 1st.
    acl_dict = {
        "description": "too_fast",
        "admin_state_up": True,
        "tenant_id": "1",
        "match_condition": "!too_fast",
        "listener_id": "1efa3b31-9d05-4cc3-ab5c-6a9add115d40",
        "operator": "tcp-request content",
        "match": "accept",
        "action": "fe_sess_rate",
        "acl_type": "Rate",
        "id": "5529d9f9-f9b7-4467-affa-1d77324dbb15",
        "condition": "ge 10",
        "name": "too_fast"
    }
    TEST.v2_api_acls.add(acl_dict)
    TEST.v2_acls.add(lbaas_v2.Acl(acl_dict))
