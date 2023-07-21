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

import os_vif
from os_vif import exception as vif_exc
from os_vif.objects import instance_info
from os_vif.objects import network
from os_vif.objects import subnet as os_subnet
from os_vif.objects import vif as vif_obj
from oslo_log import log as logging
from oslo_utils import uuidutils

LOG = logging.getLogger(__name__)

TAP_DEVICE_PREFIX = 'test-'
BR_DEVICE_PREFIX = 'br-test-'
LINUX_DEV_LEN = 14


class OSVifClient(object):

    def __init__(self):
        os_vif.initialize()

    def plug_port(self, port, subnets):
        instance_info = self._get_instance_info(port)
        os_vif_object = self._get_vif_object(port, subnets)
        try:
            os_vif.plug(os_vif_object, instance_info)
        except vif_exc.PlugException as err:
            LOG.error('Failed to plug port %s on the host. Error: %s',
                      port['name'], err)

    def _get_instance_info(self, port):
        return instance_info.InstanceInfo(
            uuid=uuidutils.generate_uuid(),
            name='fake-vm-connected-to-%s' % port['name'],
            project_id=port['project_id'])

    def _get_subnet_objects(self, port, subnets):
        cidrs = []
        os_vif_subnets = []
        for fixed_ip in port['fixed_ips']:
            subnet = subnets.get(fixed_ip['subnet_id'])
            os_vif_subnet = os_subnet.Subnet(subnet['cidr'])
            os_vif_subnets.append(os_vif_subnet)
        return os_subnet.SubnetList(os_vif_subnets)

    def _get_network_object(self, port, subnets):
        return network.Network(
            label='neutron-heater-test-net',
            subnets=self._get_subnet_objects(port, subnets),
            bridge='br-int')

    def _get_vif_object(self, port, subnets):
        # NOTE(slaweq): VIFBridge is used always, even if it will be run on
        # the ML2/OVN backend in Neutron because that way port created in
        # openvswitch will actually have network device so it will have ofport
        # number which is needed to provision port by the neutron L2 agent (or
        # ovn-controller)
        return vif_obj.VIFBridge(
            id=port['id'],
            vif_name=self._get_tap_name(port),
            bridge_name=self._get_bridge_name(port),
            plugin='ovs',
            network=self._get_network_object(port, subnets),
            port_profile=self._get_port_profile(port),
            address=port['mac_address'])

    def _get_port_profile(self, port):
        return vif_obj.VIFPortProfileOpenVSwitch(
            interface_id=port['id'], create_port=True)

    def _get_tap_name(self, port):
        return (TAP_DEVICE_PREFIX + port['id'])[:LINUX_DEV_LEN]

    def _get_bridge_name(self, port):
        return (BR_DEVICE_PREFIX + port['id'])[:LINUX_DEV_LEN]

