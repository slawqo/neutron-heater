#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CLOUDS_YAML_DIR=${CLOUDS_YAML_DIR:-"${HOME}/.config/openstack"}
NEUTRON_HEATER_IMAGE=${NEUTRON_HEATER_IMAGE:-"quay.io/skaplons/neutron-heater:latest"}
CLOUD_NAME=${OS_CLOUD:-"overcloud"}

TMP_INVENTORY_FILE="/tmp/hosts"
INVENTORY_FILE=${INVENTORY_FILE:-"${SCRIPT_DIR}/../hosts"}

L2_AGENT_NAME=${L2_AGENT_NAME:-"ovn-controller"}

# Number of resources created by the neutron-heater script run ON EACH node
# So if there is 3 x compute node and 3 x controller node with L2 agent there will
# be in total:
# * 6 x $NETWORKS created in neutron
# * $PORTS created in each NETWORK
# With default values it will create in total: 60 NETWORKS and 1500 PORTS
CONCURRENCY=${CONCURRENCY:-0}
NETWORKS=${NETWORKS:-10}
PORTS=${PORTS:-25}
IPV4_SUBNETS=${IPV4_SUBNETS:-1}
IPV6_SUBNETS=${IPV6_SUBNETS:-1}

# Discover nodes with L2 agent in overcloud
/usr/bin/podman run \
    --privileged \
    -v ${CLOUDS_YAML_DIR}:/root/.config/openstack \
    -v /tmp:/tmp/ ${NEUTRON_HEATER_IMAGE} \
    discover \
    --cloud-name=${CLOUD_NAME} \
    --l2_agent_name=${L2_AGENT_NAME} \
    --insecure \
    --inventory_file_name ${TMP_INVENTORY_FILE}

if [ ! -e "${TMP_INVENTORY_FILE}" ]; then
    echo "Temporary inventory file not created."
    exit 1
fi

# Replace hostnames of the nodes to use ctlplane network to access there
/usr/bin/sed 's/redhat\.local/ctlplane\.redhat\.local/' ${TMP_INVENTORY_FILE} | /usr/bin/sed 's/$/ ansible_user=tripleo-admin/' > ${INVENTORY_FILE}

/usr/bin/ansible-playbook \
    -i ${INVENTORY_FILE} ${SCRIPT_DIR}/../playbooks/run.yaml \
    -e neutron_heater_image=${NEUTRON_HEATER_IMAGE} \
    -e neutron_heater_cloud_name=${CLOUD_NAME} \
    -e neutron_heater_concurrency=${CONCURRENCY} \
    -e neutron_heater_networks=${NETWORKS} \
    -e neutron_heater_ports=${PORTS} \
    -e neutron_heater_ipv4_subnets=${IPV4_SUBNETS} \
    -e neutron_heater_ipv6_subnets=${IPV6_SUBNETS}
