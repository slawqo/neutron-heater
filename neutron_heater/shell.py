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
import socket
import sys

from neutron_heater import openstack_client
from neutron_heater import os_vif_client


NUM_NETWORKS = 1
NUM_IPv4_SUBNETS_PER_NETWORK = 1
NUM_IPv6_SUBNETS_PER_NETWORK = 1
NUM_PORTS_PER_NETWORK = 2

# TODO(slaweq): this should be more smart and based on the number of ports per
# network maybe
V4_CIDR_BASE = "192.168.%s.0/24"
V6_CIDR_BASE = "2000:%s::/64"

# ERROR_EXIT_CODES
NET_CREATE_FAIL = 1
SUBNET_CREATE_FAIL = 2
PORT_CREATE_FAIL = 3


def main(argv=sys.argv[1:]):
    # TODO(slaweq): add config options to specify cloud name and region name
    # properly
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud="devstack-admin",
                                       region_name="RegionOne")
    os_vif = os_vif_client.OSVifClient()

    for net in range(NUM_NETWORKS):
        network_name = "network-%s-host-%s" % (net, hostname)
        network = client.create_network(network_name)
        if not network:
            sys.exit(NET_CREATE_FAIL)
        subnets = {}
        for v4_subnet in range(NUM_IPv4_SUBNETS_PER_NETWORK):
            subnet_name = "v4_subnet-%s-host-%s" % (v4_subnet, hostname)
            cidr = V4_CIDR_BASE % v4_subnet
            subnet = client.create_subnet(network['id'], subnet_name, cidr)
            if subnet:
                subnets[subnet['id']] = subnet

        for v6_subnet in range(NUM_IPv6_SUBNETS_PER_NETWORK):
            subnet_name = "v6_subnet-%s-host-%s" % (v6_subnet, hostname)
            cidr = V6_CIDR_BASE % v4_subnet
            subnet = client.create_subnet(network['id'], subnet_name, cidr)
            if subnet:
                subnets[subnet['id']] = subnet

        if subnets:
            # Only if some subnets were created creating ports makes any sense
            for port in range(NUM_PORTS_PER_NETWORK):
                port_name = "port-%s-host-%s" % (port, hostname)
                port = client.create_port(network['id'], port_name, hostname)
                if port:
                    os_vif.plug_port(port, subnets)


if __name__ == "__main__":
    main()
