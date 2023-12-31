FROM quay.io/centos/centos:stream9

ENV PYTHON="python3"
ENV NEUTRON_HEATER_GIT="https://github.com/slawqo/neutron-heater.git"
ENV NEUTRON_HEATER_DIR="/neutron-heater"
ENV NEUTRON_HEATER_BRANCH="main"

ENV INSTALL_PACKAGES="dnf install -y"

RUN ${INSTALL_PACKAGES} git
RUN ${INSTALL_PACKAGES} sudo
RUN ${INSTALL_PACKAGES} ${PYTHON}
RUN ${INSTALL_PACKAGES} ${PYTHON}-devel
RUN ${INSTALL_PACKAGES} ${PYTHON}-setuptools

RUN git clone ${NEUTRON_HEATER_GIT} ${NEUTRON_HEATER_DIR} --branch ${NEUTRON_HEATER_BRANCH}

WORKDIR ${NEUTRON_HEATER_DIR}
RUN ${PYTHON} setup.py install
RUN ${PYTHON} -m pip install -r requirements.txt

RUN ln -s /usr/local/bin/privsep-helper /usr/bin/privsep-helper

ENTRYPOINT ["neutron-heater"]
