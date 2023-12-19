Heater_run
=============

This role runs podman container with neutron-heater to create Neutron resources in the cloud

Role Variables
--------------

| Variable                 | Required | Default                                  | Comments                                                                     |
|-----------------------------|----------|------------------------------------------|---------------------------------------------------------------------------|
| neutron_heater_venv_path    | no       | /opt/stack/neutron-heater/.venv | Path of the virtual env which will be used to install neutron-heater               |
| neutron_heater_cloud_name   | no       | devstack-admin                  | cloud name to be used, it needs to be defined in the clouds.yaml file              |
| neutron_heater_region_name  | no       | RegionOne                       | Region Name to be used                                                             |
| neutron_heater_concurrency  | no       | 0                               | number of threads run at once by neutron-heater                                    |
| neutron_heater_networks     | no       | 10                              | number of networks to be created by neutron-heater tool                            |
| neutron_heater_ports        | no       | 25                              | number of ports to be created in each network created by the neutron-heater        |
| neutron_heater_ipv4_subnets | no       | 1                               | number of IPv4 subnets to be created in each network created by the neutron-heater |
| neutron_heater_ipv6_subnets | no       | 1                               | number of IPv6 subnets to be created in each network created by the neutron-heater |

Example Playbook
----------------

    - hosts: compute_nodes
      roles:
         - { role: heater_run }

License
-------

BSD

Author Information
------------------

Slawek Kaplonski
https://kaplonski.pl
