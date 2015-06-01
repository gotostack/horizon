# Copyright 2014 Letv Cloud Computing
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

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters


class LbaasV2AgentsFilterAction(tables.FilterAction):

    def filter(self, table, agents, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [ag for ag in agents
                if q in ag.agent_type.lower()]


class LbaasV2AgentsTable(tables.DataTable):
    host = tables.Column("host",
                         verbose_name=_("Host"),
                         link='horizon:manager:lbaas_v2_agents:detail')
    agent_type = tables.Column("agent_type",
                               verbose_name=_("Agent Type"))
    alive = tables.Column("alive",
                          verbose_name=_("Alive"))
    topic = tables.Column("topic",
                          verbose_name=_("Topic"))
    binary = tables.Column("binary",
                           verbose_name=_("Binary Service"))
    description = tables.Column('description', verbose_name=_("Description"))
    admin_state_up = tables.Column('admin_state_up',
                                   verbose_name=_("Admin State"))
    heartbeat_timestamp = tables.Column("heartbeat_timestamp",
                                        verbose_name=_("Heartbeat Timestamp"))
    started = tables.Column("started_at",
                            verbose_name=_("Time since started"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})
    created = tables.Column("created_at",
                            verbose_name=_("Time since created"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})

    def get_object_display(self, datum):
        return datum.binary

    def get_object_id(self, datum):
        return datum.id

    class Meta(object):
        name = "lbaas_v2_agents"
        verbose_name = _("Load Balancing v2 Agents")
        table_actions = (LbaasV2AgentsFilterAction,)
