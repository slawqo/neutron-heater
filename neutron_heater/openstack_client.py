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


import netaddr
import openstack
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class OSClient(object):

    def __init__(self, cloud, region_name):
        self._os_conn = None
        self.cloud = cloud
        self.region_name = region_name

    @property
    def os_conn(self):
        if self._os_conn is None:
            self._os_conn = openstack.connect(cloud=self.cloud,
                                              region_name=self.region_name)
        return self._os_conn

    def create_network(self, name):
        try:
            return self.os_conn.network.create_network(name=name)
        except Exception as e:
            LOG.warning("Network %s creation failed. Error: %s", name, e)

    def create_subnet(self, network_id, name, cidr):
        ip_version = netaddr.IPNetwork(cidr).version
        try:
            return self.os_conn.network.create_subnet(network_id=network_id,
                                                      name=name,
                                                      ip_version=ip_version,
                                                      cidr=cidr)
        except Exception as e:
            LOG.warning("Subnet %s creation in network %s failed. "
                        "Error: %s", name, network_id, e)

    def create_port(self, network_id, name, hostname=None):
        kwargs = {
            'network_id': network_id,
            'name': name
        }
        if hostname:
            kwargs['device_owner'] = 'compute:neutron_heater'
            kwargs['binding_host_id'] = hostname
        try:
            return self.os_conn.network.create_port(**kwargs)
        except Exception as e:
            LOG.warning("Port %s creation in network %s failed. "
                        "Error: %s", name, network_id, e)


