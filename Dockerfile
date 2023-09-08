FROM python:3

ENV PYTHON=python3
ENV NEUTRON_HEATER_GIT=https://github.com/slawqo/neutron-heater.git
ENV NEUTRON_HEATER_DIR=/neutron-heater

RUN git clone ${NEUTRON_HEATER_GIT} ${NEUTRON_HEATER_DIR}

WORKDIR ${NEUTRON_HEATER_DIR}
RUN ${PYTHON} setup.py install
RUN ${PYTHON} -m pip install -r requirements.txt

ENTRYPOINT ["neutron-heater"]
