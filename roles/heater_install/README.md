Heater_install
==============

This role clones neutron-heater repository and installs it in the specified virtual environment

Role Variables
--------------

| Variable                 | Required | Default                                  | Comments                                                             |
|--------------------------|----------|------------------------------------------|----------------------------------------------------------------------|
| neutron_heater_repo      | no       | https://github.com/slawqo/neutron-heater | Address of the source repository                                     |
| neutron_heater_version   | no       | main                                     | Name of the branch, tag, or commit hash                              |
| neutron_heater_dest_path | no       | /opt/stack/neutron-heater                | Destination path to clone neutron-heater                             |
| neutron_heater_venv_path | no       | {{ neutron_heater_dest_path }}/.venv     | Path of the virtual env which will be used to install neutron-heater |

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: compute_nodes
      roles:
         - { role: heater_install }

License
-------

BSD

Author Information
------------------

Slawek Kaplonski
https://kaplonski.pl
