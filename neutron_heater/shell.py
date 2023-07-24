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
        cfg.IntOpt('networks',
                   default=10,
                   help='Number of networks to be created in Neutron'),
        cfg.IntOpt('ipv4_subnets',
                   default=1,
                   help='Number of IPv4 subnets to be created in Neutron for '
                        'each created network. It only has effect with '
                        '"create" action.'),
        cfg.IntOpt('ipv6_subnets',
                   default=1,
                   help='Number of IPv6 subnets to be created in Neutron for '
                        'each created network. It only has effect with '
                        '"create" action.'),
        cfg.IntOpt('ports',
                   default=10,
                   help='Number of ports to be created in Neutron for '
                        'each created network. Those ports will be bound '
                        'and provisioned on all nodes with the L2 agents '
                        'running. It only has effect with "create" action.'),
        cfg.StrOpt('cloud-name',
                   default='devstack-admin',
                   dest='cloud_name',
                   help="Cloud's name to be used. It has to be defined in "
                        "the clouds.yaml file."),
        cfg.StrOpt('region-name',
                   default='RegionOne',
                   dest='region_name',
                   help="Cloud's region name."),
    ]
    conf.register_cli_opts(options)


def register_logging_config(conf):
    logging.register_options(conf)
    logging.setup(conf, NAME)


def get_network_name(index, hostname):
    return "network-%s-host-%s" % (index, hostname)


def create_network_with_ports(config):
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud=config.cloud_name,
                                       region_name=config.region_name)
    os_vif = os_vif_client.OSVifClient()

    for net in range(config.networks):
        network = client.create_network(get_network_name(net, hostname))
        if not network:
            sys.exit(NET_CREATE_FAIL)
        subnets = {}
        for v4_subnet in range(config.ipv4_subnets):
            subnet_name = "v4_subnet-%s-host-%s" % (v4_subnet, hostname)
            cidr = V4_CIDR_BASE % v4_subnet
            subnet = client.create_subnet(network['id'], subnet_name, cidr)
            if subnet:
                subnets[subnet['id']] = subnet

        for v6_subnet in range(config.ipv6_subnets):
            subnet_name = "v6_subnet-%s-host-%s" % (v6_subnet, hostname)
            cidr = V6_CIDR_BASE % v4_subnet
            subnet = client.create_subnet(network['id'], subnet_name, cidr)
            if subnet:
                subnets[subnet['id']] = subnet

        if subnets:
            # Only if some subnets were created creating ports makes any sense
            for port in range(config.ports):
                port_name = "port-%s-host-%s" % (port, hostname)
                port = client.create_port(network['id'], port_name, hostname)
                if port:
                    os_vif.plug_port(port, subnets)

def clean_all(config):
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud=config.cloud_name,
                                       region_name=config.region_name)
    os_vif = os_vif_client.OSVifClient()
    all_networks = client.get_networks()
    expected_network_names = [get_network_name(net, hostname) for
                              net in range(config.networks)]
    for network in all_networks:
        if network['name'] not in expected_network_names:
            continue
        ports = client.get_ports(network['id'])
        for port in ports:
            subnets = client.get_port_subnets(port)
            os_vif.unplug_port(port, subnets)
            client.delete_port(port)
        client.delete_network(network)


def main(argv=sys.argv[1:]):
    config = cfg.CONF
    register_config_options(config)
    register_logging_config(config)
    config(argv)
    if config.action == CREATE:
        LOG.info("Starting resource creation")
        create_network_with_ports(config)
        LOG.info("Resources created")
    elif config.action == CLEAN:
        LOG.info("Starting resource cleanup")
        clean_all(config)
        LOG.info("Resources cleaned")
    else:
        config.print_help()
        sys.exit(INVALID_CONFIG_OPTION)


if __name__ == "__main__":
    main()
