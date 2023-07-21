2. Edit the ``/etc/neutron_heater/neutron_heater.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://neutron_heater:NEUTRON_HEATER_DBPASS@controller/neutron_heater
