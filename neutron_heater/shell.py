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

from concurrent import futures
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
        cfg.IntOpt('concurrency',
                   default=0,
                   help='Number of threads in which networks and resources '
                        'which belongs to network will be created. '
                        'Each thread will create one network and all subnets '
                        'and ports which should be created per network. '
                        'Default value is "0" which means it will be '
                        'calculated automatically based on the "networks" '
                        'value.'),
    ]
    conf.register_cli_opts(options)


def register_logging_config(conf):
    logging.register_options(conf)
    logging.setup(conf, NAME)


def get_network_name(index, hostname):
    return "network-%s-host-%s" % (index, hostname)


def create_network_with_ports(net_number, ipv4_subnets, ipv6_subnets, ports,
                              hostname, os_client, os_vif):
    network_name = get_network_name(net_number, hostname)
    LOG.info("Starting to create network %s" % network_name)
    network = os_client.create_network(network_name)
    if not network:
        LOG.error("Failed to create network. Stopping worker.")
        return False
    subnets = {}
    for v4_subnet in range(ipv4_subnets):
        subnet_name = "v4_subnet-%s-host-%s" % (v4_subnet, hostname)
        cidr = V4_CIDR_BASE % v4_subnet
        subnet = os_client.create_subnet(network['id'], subnet_name, cidr)
        if subnet:
            subnets[subnet['id']] = subnet

    for v6_subnet in range(ipv6_subnets):
        subnet_name = "v6_subnet-%s-host-%s" % (v6_subnet, hostname)
        cidr = V6_CIDR_BASE % v4_subnet
        subnet = os_client.create_subnet(network['id'], subnet_name, cidr)
        if subnet:
            subnets[subnet['id']] = subnet

    if subnets:
        # Only if some subnets were created creating ports makes any sense
        for port in range(ports):
            port_name = "port-%s-host-%s" % (port, hostname)
            port = os_client.create_port(network['id'], port_name, hostname)
            if port:
                os_vif.plug_port(port, subnets)
    return True


def create_resources(config):
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud=config.cloud_name,
                                       region_name=config.region_name)
    os_vif = os_vif_client.OSVifClient()

    workers = config.concurrency or config.networks
    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        [executor.submit(
            create_network_with_ports,
            net, config.ipv4_subnets, config.ipv6_subnets, config.ports,
            hostname, client, os_vif) for net in range(config.networks)]


def clean_network_with_ports(network, os_client, os_vif):
    ports = os_client.get_ports(network['id'])
    for port in ports:
        subnets = os_client.get_port_subnets(port)
        os_vif.unplug_port(port, subnets)
        os_client.delete_port(port)
    os_client.delete_network(network)


def clean_all(config):
    hostname = socket.gethostname()
    client = openstack_client.OSClient(cloud=config.cloud_name,
                                       region_name=config.region_name)
    os_vif = os_vif_client.OSVifClient()
    all_networks = client.get_networks()
    expected_network_names = [get_network_name(net, hostname) for
                              net in range(config.networks)]
    networks_to_clean = [network for network in all_networks if
                         network['name'] in expected_network_names]
    workers = config.concurrency or config.networks
    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        [executor.submit(
            clean_network_with_ports, network, client, os_vif) for
            network in networks_to_clean]


def main(argv=sys.argv[1:]):
    config = cfg.CONF
    register_config_options(config)
    register_logging_config(config)
    config(argv)
    if config.action == CREATE:
        LOG.info("Starting resource creation")
        create_resources(config)
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
