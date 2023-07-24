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

from oslo_config import cfg
from oslo_log import log as logging

from neutron_heater import openstack_client
from neutron_heater import os_vif_client


LOG = logging.getLogger(__name__)

NAME = "Neutron heater"

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
INVALID_CONFIG_OPTION = 10

# ACTIONS POSSIBLE TO DO
CREATE = 'create'
CLEAN = 'clean'


def register_config_options(conf):
    options = [
        cfg.StrOpt('action',
                   choices=[CREATE, CLEAN],
                   positional=True,
                   help='Action to do. Possible options are "create" to '
                        'create resources in neutron and on the nodes or '
                        '"clean" to clean all resources made earlier by this '
                        'tool.'),
    ]
    conf.register_cli_opts(options)


def register_logging_config(conf):
    logging.register_options(conf)
    logging.setup(conf, NAME)

def get_network_name(index, hostname):
    return "network-%s-host-%s" % (index, hostname)


def create_network_with_ports():
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud="devstack-admin",
                                       region_name="RegionOne")
    os_vif = os_vif_client.OSVifClient()

    for net in range(NUM_NETWORKS):
        network = client.create_network(get_network_name(net, hostname))
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

def clean_all():
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud="devstack-admin",
                                       region_name="RegionOne")
    os_vif = os_vif_client.OSVifClient()
    all_networks = client.get_networks()
    for net in range(NUM_NETWORKS):
        expected_network_name = get_network_name(net, hostname)
        for network in all_networks:
            if network['name'] != expected_network_name:
                continue
            ports = client.get_ports(network['id'])
            for port in ports:
                subnets = client.get_port_subnets(port)
                os_vif.unplug_port(port, subnets)
                client.delete_port(port)
            client.delete_network(network)



def main(argv=sys.argv[1:]):
    # TODO(slaweq): add config options to specify cloud name and region name
    # properly
    config = cfg.CONF
    register_config_options(config)
    register_logging_config(config)
    config(sys.argv[1:])
    if config.action == CREATE:
        LOG.info("Starting resource creation")
        create_network_with_ports()
        LOG.info("Resources created")
    elif config.action == CLEAN:
        LOG.info("Starting resource cleanup")
        clean_all()
        LOG.info("Resources cleaned")
    else:
        config.print_help()
        sys.exit(INVALID_CONFIG_OPTION)


if __name__ == "__main__":
    main()
