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
import re
import socket
import sys
import yaml

from oslo_log import log as logging

from neutron_heater import conf
from neutron_heater import constants
from neutron_heater import openstack_client
from neutron_heater import os_vif_client


LOG = logging.getLogger(__name__)


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
        cidr = constants.V4_CIDR_BASE % v4_subnet
        subnet = os_client.create_subnet(network['id'], subnet_name, cidr)
        if subnet:
            subnets[subnet['id']] = subnet

    for v6_subnet in range(ipv6_subnets):
        subnet_name = "v6_subnet-%s-host-%s" % (v6_subnet, hostname)
        cidr = constants.V6_CIDR_BASE % v4_subnet
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


def _get_osclient(config):
    kwargs = {'cloud': config.cloud_name}
    if config.region_name is not None:
        kwargs['region_name'] = config.region_name
    if config.insecure is True:
        kwargs['verify'] = False
    return openstack_client.OSClient(**kwargs)


def create_resources(config):
    hostname = socket.gethostname()
    client = _get_osclient(config)
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
    client = _get_osclient(config)
    os_vif = os_vif_client.OSVifClient()
    all_networks = client.get_networks()
    networks_to_clean = []
    expected_network_name_pattern = re.compile(
        r"network-\d+-host-%s" % hostname)
    for network in all_networks:
        if expected_network_name_pattern.match(network['name']):
            networks_to_clean.append(network)
    workers = config.concurrency or config.networks
    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        [executor.submit(
            clean_network_with_ports, network, client, os_vif) for
            network in networks_to_clean]


def write_inventory_file(hosts, filename):
    if filename.endswith(".yaml") or filename.endswith("yml"):
        write_yaml_file(hosts, filename)
    else:
        write_ini_file(hosts, filename)


def write_yaml_file(hosts, filename):
    content = {"all": {"hosts": {}}}
    for host in hosts:
        content["all"]["hosts"][host] = None

    yaml.SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar(
            'tag:yaml.org,2002:null', '')
    )
    with open(filename, 'w',) as f:
        yaml.safe_dump(content, f, default_flow_style=False)


def write_ini_file(hosts, filename):
    with open(filename, "w") as f:
        f.writelines(hosts)


def discover_hosts(config):
    client = _get_osclient(config)
    agents = client.get_agents(config.l2_agent_name)
    if not agents:
        sys.exit(constants.NO_AGENTS_FOUND)
    hosts = []
    for agent in agents:
        hosts.append(agent.host)
    write_inventory_file(hosts, config.inventory_file_name)


def set_unlimited_quotas(config):
    client = _get_osclient(config)
    client.set_project_quota(networks=-1, subnets=-1, ports=-1)


def main(argv=sys.argv[1:]):
    config = conf.get_config(argv)
    if config.action == constants.CREATE:
        LOG.info("Starting resource creation")
        set_unlimited_quotas(config)
        create_resources(config)
        LOG.info("Resources created")
    elif config.action == constants.CLEAN:
        LOG.info("Starting resource cleanup")
        clean_all(config)
        LOG.info("Resources cleaned")
    elif config.action == constants.DISCOVER_HOSTS:
        LOG.info("Starting discovering hosts for inventory file")
        discover_hosts(config)
        LOG.info("Inventory file ready.")
    else:
        config.print_help()
        sys.exit(constants.INVALID_CONFIG_OPTION)


if __name__ == "__main__":
    main()
