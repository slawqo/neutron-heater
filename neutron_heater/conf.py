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

from oslo_config import cfg
from oslo_log import log as logging

from neutron_heater import constants


def register_config_options(conf):
    options = [
        cfg.StrOpt('action',
                   choices=[constants.CREATE, constants.CLEAN,
                            constants.DISCOVER_HOSTS],
                   positional=True,
                   help='Action to do. Possible options are "create" to '
                        'create resources in neutron and on the nodes, '
                        '"clean" to clean all resources made earlier by this '
                        'tool or "discover" to discover all hosts with L2 '
                        'agent installed and prepare inventory file for '
                        'ansible to run there.'),
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
        cfg.StrOpt('l2_agent_name',
                   default='ovn-controller',
                   help="Name of the L2 agent's binary. It's used only with "
                        "the 'discover' action."),
        cfg.StrOpt('inventory_file_name',
                   default='hosts',
                   help="Name of the file where ansible inventory will be "
                        "stored."),
    ]
    conf.register_cli_opts(options)


def register_logging_config(conf):
    logging.register_options(conf)
    logging.setup(conf, constants.NAME)


def get_config(argv):
    config = cfg.CONF
    register_config_options(config)
    register_logging_config(config)
    config(argv)
    return config
