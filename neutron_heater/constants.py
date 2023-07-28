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

NAME = "Neutron heater"

# ACTIONS POSSIBLE TO DO
CREATE = 'create'
CLEAN = 'clean'

# TODO(slaweq): this should be more smart and based on the number of ports per
# network maybe
V4_CIDR_BASE = "192.168.%s.0/24"
V6_CIDR_BASE = "2000:%s::/64"

# ERROR_EXIT_CODES
INVALID_CONFIG_OPTION = 1
