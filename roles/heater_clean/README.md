Heater_clean
=============

This role runs podman container with neutron-heater to clean Neutron resources created by the Neutron-heater tool previously

Role Variables
--------------

| Variable                 | Required | Default                                  | Comments                                                                     |
|-----------------------------|----------|------------------------------------------|---------------------------------------------------------------------------|
| neutron_heater_venv_path    | no       | /opt/stack/neutron-heater/.venv | Path of the virtual env which will be used to install neutron-heater               |
| neutron_heater_cloud_name   | no       | devstack-admin                  | cloud name to be used, it needs to be defined in the clouds.yaml file              |
| neutron_heater_region_name  | no       | RegionOne                       | Region Name to be used                                                             |
| neutron_heater_concurrency  | no       | 0                               | number of threads run at once by neutron-heater                                    |

Example Playbook
----------------

    - hosts: compute_nodes
      roles:
         - { role: heater_clean }

License
-------

BSD

Author Information
------------------

Slawek Kaplonski
https://kaplonski.pl
